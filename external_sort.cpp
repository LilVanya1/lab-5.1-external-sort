#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <algorithm>
#include <queue>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <filesystem>

using namespace std;

// Глобальные флаги, которые настраивают логику сортировки
int sort_column = 0;          // Индекс колонки для сортировки (от 0 до 21)
bool is_numeric = false;      // Нужно ли сравнивать значения как числа (иначе как текст)
bool sort_descending = false; // По убыванию (true) или по возрастанию (false)

// Структура для хранения одной строки CSV файла
struct Record {
    string line;    // Сама полная строка (чтобы потом быстро записать её в итоговый файл)
    double num_val; // Вырезанное числовое значение ключа (если колонка числовая)
    string str_val; // Вырезанное текстовое значение ключа (если колонка текстовая)
};

// Функция сверхбыстрого парсинга (извлечения ключа из строки).
// Вместо медленного разбиения всей строки (split), мы просто прыгаем по запятым до нужной колонки.
inline void extract_key(Record& r, string&& line_val, int col) {
    r.line = move(line_val); // move спасает от лишнего копирования строк в оперативной памяти
    size_t start = 0;

    // Прыгаем по запятым нужное количество раз
    for (int i = 0; i < col; ++i) {
        start = r.line.find(',', start);
        if (start == string::npos) break;
        start++;
    }

    // Если нашли нужную колонку, вырезаем её содержимое
    if (start != string::npos) {
        size_t end = r.line.find(',', start);
        string val = (end == string::npos) ? r.line.substr(start) : r.line.substr(start, end - start);

        if (is_numeric) {
            char* p;
            // strtod - системная C-функция, переводит строку в число в разы быстрее, чем stod из C++
            r.num_val = strtod(val.c_str(), &p);
        } else {
            r.str_val = move(val);
        }
    } else {
        r.num_val = 0.0;
        r.str_val = "";
    }
}

// Компаратор (правило сравнения) для встроенного алгоритма std::sort (сортировка в памяти)
bool cmp(const Record& a, const Record& b) {
    if (is_numeric) {
        // Если убывание - знак >, если возрастание - знак <
        return sort_descending ? a.num_val > b.num_val : a.num_val < b.num_val;
    }
    // Лексикографическое (алфавитное) сравнение для текста
    return sort_descending ? a.str_val > b.str_val : a.str_val < b.str_val;
}

// Структура элемента для приоритетной очереди (Кучи) на этапе слияния
struct HeapItem {
    Record rec;
    int idx; // Индекс временного файла, из которого пришла эта строка (чтобы знать, откуда читать следующую)

    // Перегрузка оператора ">".
    // std::priority_queue в C++ по умолчанию является Max-Heap (выдает самое БОЛЬШОЕ значение).
    // Мы инвертируем логику, чтобы сделать из неё Min-Heap (или обратно Max-Heap, если юзер выбрал убывание).
    bool operator>(const HeapItem& b) const {
        if (is_numeric) {
            return sort_descending ? rec.num_val < b.rec.num_val : rec.num_val > b.rec.num_val;
        }
        return sort_descending ? rec.str_val < b.rec.str_val : rec.str_val > b.rec.str_val;
    }
};

class Sorter {
    size_t mem_limit;       // Лимит оперативной памяти на один кусок
    vector<string> temps;   // Список имен созданных временных файлов
    string header;          // Заголовок CSV (первая строка)
    string temp_dir;        // Временная папка для temp-файлов

public:
    Sorter(size_t mb) : mem_limit(mb * 1024 * 1024) {
        // Создаём временную папку в системной директории
        temp_dir = filesystem::temp_directory_path().string() + "/ext_sort_tmp";
        filesystem::create_directories(temp_dir);
    }

    // Деструктор класса (срабатывает при уничтожении объекта). Гарантирует удаление временных файлов при краше.
    ~Sorter() {
        clean_temp_files();
    }

    // Сохранение куска данных из ОЗУ на жесткий диск
    void save(vector<Record>& data, int num) {
        // Сортируем массив данных с помощью алгоритма IntroSort (гибрид QuickSort и HeapSort)
        sort(data.begin(), data.end(), cmp);

        string name = "temp_" + to_string(num) + ".csv";
        ofstream out(name, ios::binary);

        // Пишем отсортированные строки
        for (const auto& r : data) out << r.line << "\n";

        temps.push_back(name); // Запоминаем имя файла
        cout << "Часть " << num << ": " << data.size() << "\n";
    }

    // === ЭТАП 1: РАЗБИЕНИЕ (SPLIT) ===
    double split(const string& input) {
        cout << "Этап 1: Разбиение\n";
        auto t1 = chrono::high_resolution_clock::now();

        ifstream in(input, ios::binary);
#ifdef _WIN32
        // Защита от краша на Windows: если в пути файла есть русские буквы, открываем через u8path
        if (!in.is_open()) {
            in.open(std::filesystem::u8path(input), ios::binary);
        }
#endif
        if (!in.is_open()) {
            cerr << "ОШИБКА: C++ не смог открыть входной файл: " << input << "\n";
            exit(1);
        }

        // Читаем заголовки колонок
        getline(in, header);
        if (!header.empty() && header.back() == '\r') header.pop_back(); // Чистим символ возврата каретки Windows

        vector<Record> chunk;
        chunk.reserve(500000); // Резервируем память заранее, чтобы избежать медленной реаллокации массива
        size_t sz = 0;
        int num = 0;
        string line;

        // Построчное чтение файла
        while (getline(in, line)) {
            if (!line.empty() && line.back() == '\r') line.pop_back();
            if (line.empty()) continue;

            sz += line.length() + 64; // Приблизительный подсчет веса строки в байтах + служебная память

            Record r;
            extract_key(r, move(line), sort_column); // Вытаскиваем ключ сортировки
            chunk.push_back(move(r));

            // Если размер куска достиг лимита (100 МБ) - сохраняем и очищаем память
            if (sz >= mem_limit) {
                save(chunk, num++);
                chunk.clear();
                sz = 0;
            }
        }
        // Сохраняем остатки (последний кусок файла)
        if (!chunk.empty()) save(chunk, num++);

        auto t2 = chrono::high_resolution_clock::now();
        double sec = chrono::duration<double>(t2 - t1).count();
        return sec;
    }

    // === ЭТАП 2: СЛИЯНИЕ (K-WAY MERGE) ===
    double merge(const string& output) {
        cout << "Этап 2: Слияние\n";
        auto t1 = chrono::high_resolution_clock::now();

        vector<ifstream> files(temps.size());
        // Инициализация Приоритетной очереди (Кучи)
        priority_queue<HeapItem, vector<HeapItem>, greater<HeapItem>> heap;

        // Открываем все временные файлы одновременно и кладем из каждого по первой строке в Кучу
        for (size_t i = 0; i < temps.size(); i++) {
            files[i].open(temps[i], ios::binary);
            string line;
            if (getline(files[i], line)) {
                if (!line.empty() && line.back() == '\r') line.pop_back();
                HeapItem item;
                extract_key(item.rec, move(line), sort_column);
                item.idx = i;
                heap.push(move(item)); // Добавление элемента в кучу O(log N)
            }
        }

        ofstream out(output, ios::binary);
#ifdef _WIN32
        if (!out.is_open()) {
            out.open(std::filesystem::u8path(output), ios::binary);
        }
#endif
        if (!out.is_open()) {
            cerr << "ОШИБКА: C++ не смог создать итоговый файл: " << output << "\n";
            exit(1);
        }

        out << header << "\n"; // Пишем заголовки обратно

        long long cnt = 0;
        // Главный цикл слияния
        while (!heap.empty()) {
            HeapItem item = heap.top(); // Берем минимальный (или максимальный) элемент из всех файлов
            heap.pop(); // Удаляем его из кучи

            out << item.rec.line << "\n"; // Пишем его в итоговый файл
            cnt++;

            if (cnt % 500000 == 0) cout << "Записано: " << cnt << "\n"; // Логируем прогресс для Питона

            // Читаем следующую строку из того же файла, откуда пришел этот элемент
            string line;
            if (getline(files[item.idx], line)) {
                if (!line.empty() && line.back() == '\r') line.pop_back();
                HeapItem next;
                extract_key(next.rec, move(line), sort_column);
                next.idx = item.idx; // Сохраняем индекс файла
                heap.push(move(next)); // Кидаем новую строку в кучу
            }
        }

        // Строго закрываем потоки ВСЕХ файлов, иначе Windows не даст их удалить
        out.close();
        for (size_t i = 0; i < files.size(); i++) {
            if (files[i].is_open()) files[i].close();
        }

        // Удаляем временный мусор немедленно
        cout << "Удаление временных файлов..." << "\n";
        clean_temp_files();

        auto t2 = chrono::high_resolution_clock::now();
        return chrono::duration<double>(t2 - t1).count();
    }

    // Удаление временных файлов (temp_0.csv, temp_1.csv...)
    void clean_temp_files() {
        for (const auto& f : temps) {
            remove(f.c_str());
        }
        temps.clear();
    }

    // Функция - менеджер, вызывающая оба этапа
    void run(const string& input, const string& output, int col) {
        sort_column = col;
        // Перечисление индексов всех колонок с числами, чтобы парсер понимал, где нужно использовать strtod
        is_numeric = (col == 0 || col == 3 || col == 5 || col == 6 || col == 7 || col == 10 || col == 12 || col == 15 || col == 16 || col == 17 || col == 18);

        auto t1 = chrono::high_resolution_clock::now();
        double s = split(input);
        double m = merge(output);
        auto t2 = chrono::high_resolution_clock::now();

        // Вывод статистики. Выводится в stdout (консоль), которую потом читает Python
        cout << "\n========================================\n";
        cout << "Разбиение: " << s << " сек\n";
        cout << "Слияние: " << m << " сек\n";
        cout << "Всего: " << chrono::duration<double>(t2 - t1).count() << " сек\n";
        cout << "========================================\n";
    }
};

int main(int argc, char* argv[]) {
    // Оптимизация спортивного программирования: отключаем синхронизацию потоков ввода-вывода C и C++
    // Это делает cin и cout примерно в 3 раза быстрее
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    string inp = "alcoholics.csv";
    string out = "sorted_cpp.csv";
    int col = 0;

    // Читаем аргументы командной строки, переданные Питоном через subprocess
    if (argc > 1) inp = argv[1];
    if (argc > 2) out = argv[2];
    if (argc > 3) col = stoi(argv[3]);
    if (argc > 4) sort_descending = (stoi(argv[4]) == 1);

    // Запускаем сортировку, ограничив 1 кусок в 100 МБ ОЗУ
    Sorter s(100);
    s.run(inp, out, col);

    return 0;
}