import csv
import os
import heapq
import time


# heapq по умолчанию всегда является Min-Heap (выдает самое маленькое).
class SortKey:
    def __init__(self, key, reverse=False):
        self.key = key
        self.reverse = reverse

    # Магический метод сравнения "Меньше чем" (<)
    def __lt__(self, other):
        if self.reverse:
            return self.key > other.key # Инвертируем сравнение для убывания
        return self.key < other.key

class ExternalSort:
    def __init__(self, memory_limit_mb=100):
        # Ограничение памяти в байтах
        self.memory_limit_bytes = memory_limit_mb * 1024 * 1024
        self.temp_files = [] # Хранилище имен временных файлов
        self.header = []
        self.sort_col = 0
        self.is_numeric = False
        self.reverse = False

    # Входная точка алгоритма
    def sort(self, input_file, output_file, sort_col, reverse=False):
        self.sort_col = sort_col
        self.reverse = reverse

        # Заранее прописываем, какие колонки содержат математические числа
        # 24 столбца без отдельного «name»; индексы сдвинуты на −1 после surname
        self.is_numeric = sort_col in [0, 3, 5, 6, 7, 10, 12, 15, 16, 17, 18]

        total_start = time.time()

        # ЭТАП 1: Разбиение гигабайтного файла на 100МБ куски
        t_split_start = time.time()
        self._split(input_file)
        split_time = time.time() - t_split_start

        # ЭТАП 2: Слияние кусков обратно
        t_merge_start = time.time()
        self._merge(output_file)
        merge_time = time.time() - t_merge_start

        total_time = time.time() - total_start
        return split_time, merge_time, total_time

    def _split(self, input_file):
        chunk = [] # Массив для хранения строк в оперативной памяти
        current_size = 0
        file_index = 0

        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            try:
                self.header = next(reader) # Сохраняем заголовок
            except StopIteration:
                return

            for row in reader:
                chunk.append(row)
                # Подсчет занимаемой памяти (длина символов + количество запятых/элементов)
                current_size += sum(len(item) for item in row) + len(row)

                # Если кусок занял весь разрешенный лимит ОЗУ
                if current_size >= self.memory_limit_bytes:
                    self._save_chunk(chunk, file_index) # Сортируем и сохраняем на диск
                    file_index += 1
                    chunk = [] # Очищаем ОЗУ для следующего куска
                    current_size = 0

            # Если после цикла файл закончился, а в ОЗУ остались строки - сохраняем их как последний кусок
            if chunk:
                self._save_chunk(chunk, file_index)

    def _save_chunk(self, chunk, file_index):
        # Используем встроенную функцию sort (в Python под капотом используется супербыстрый алгоритм Timsort)
        if self.is_numeric:
            # Сортируем по значению как float (дробное число)
            chunk.sort(key=lambda x: float(x[self.sort_col]) if x[self.sort_col] else 0.0, reverse=self.reverse)
        else:
            # Сортируем как обычный текст
            chunk.sort(key=lambda x: x[self.sort_col], reverse=self.reverse)

        # Формируем имя файла и запоминаем его
        temp_name = f"temp_py_{file_index}.csv"
        self.temp_files.append(temp_name)

        # Пишем отсортированные данные в CSV файл
        with open(temp_name, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(chunk)

    def _merge(self, output_file):
        # Открываем одновременно все созданные временные файлы для чтения
        file_pointers = [open(f, 'r', encoding='utf-8') for f in self.temp_files]
        readers = [csv.reader(fp) for fp in file_pointers]

        heap = [] # Наша приоритетная очередь (Куча)

        # Вспомогательная функция для упаковки данных в Кучу
        def make_heap_item(row, reader_idx):
            val = row[self.sort_col]
            key = float(val) if self.is_numeric and val else (val if val else "")

            # Мы оборачиваем ключ в SortKey для учета направления сортировки.
            # reader_idx (номер файла) передается для того, чтобы в случае одинаковых ключей (например, 2 человека с бюджетом 1000),
            # heapq сравнивал индексы файлов, а не пытался сравнивать массивы строк (что вызовет ошибку).
            return (SortKey(key, self.reverse), reader_idx, row)

        # Читаем по одной первой строке из КАЖДОГО файла и кидаем в кучу
        for i, reader in enumerate(readers):
            try:
                row = next(reader)
                heapq.heappush(heap, make_heap_item(row, i)) # O(log N)
            except StopIteration:
                pass

        # Открываем финальный файл для записи результата
        with open(output_file, 'w', encoding='utf-8', newline='') as out_f:
            writer = csv.writer(out_f)
            writer.writerow(self.header)

            # Пока куча не опустеет
            while heap:
                # Достаем самый минимальный (или максимальный) элемент
                key_obj, reader_idx, row = heapq.heappop(heap)
                writer.writerow(row) # Записываем строку в финальный файл

                try:
                    # И читаем следующую строку из ТОГО ЖЕ файла, откуда пришла извлеченная строка
                    next_row = next(readers[reader_idx])
                    heapq.heappush(heap, make_heap_item(next_row, reader_idx))
                except StopIteration:
                    pass # Если файл кончился - ничего страшного, куча будет потихоньку уменьшаться

        # ЗАКРЫВАЕМ ВСЕ ПОТОКИ ЧТЕНИЯ. Без этого Windows запретит удалять файлы
        for fp in file_pointers:
            fp.close()

        # Удаляем гигабайты временного мусора прямо сейчас
        self.cleanup()

    # Безопасное удаление файлов с помощью модуля OS
    def cleanup(self):
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception:
                pass
        self.temp_files.clear() # Очищаем массив имен