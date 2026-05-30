# Лабораторная 5.1 — внешняя сортировка

**Студент:** Изместьев М.Н., гр. ИВТб-1302-06-00  
**Тема:** External Sort (Python + C++), CSV > RAM  
**GitHub (upload):** `lab-5.1-external-sort`

## Статус

| Компонент | Статус |
|-----------|--------|
| `external_sort.py` / `external_sort.cpp` | ✅ |
| `generator.py`, `dictionary.txt` | ✅ |
| `gui_app.py` (3 вкладки) | ✅ |
| MinGW в `_tools/mingw64/` (автопоиск g++) | ✅ |
| Отчёт `report/main.tex` | ✅ |
| Скрины `report/img/1.png`…`4.png` | ✅ |
| Файл ≥ 1 ГБ для демо | ⚠️ опционально (есть `alcoholics.csv` ~2 МБ) |
| Ссылка на GitHub в отчёте | ❌ |

## Структура

```
lab5/
├── external_sort.py
├── external_sort.cpp
├── generator.py
├── gui_app.py
├── main.py
├── dictionary.txt
├── drawio/           # схемы алгоритма (не в отчёт)
└── report/
    ├── main.tex
    └── img/          # 1–4.png
```

## Запуск

```powershell
cd c:\Users\stud222640\Documents\proga
.\.venv\Scripts\python.exe lab5\gui_app.py
```

CLI:
```powershell
.\.venv\Scripts\python.exe lab5\external_sort.py --input lab5\alcoholics.csv --output lab5\sorted.csv
```

C++ (через GUI или вручную после компиляции):
```powershell
# g++ из _tools/mingw64 или PATH
g++ -O2 -o lab5\external_sort.exe lab5\external_sort.cpp
```

## Скрины для отчёта

| # | Что |
|---|-----|
| 1 | Вкладка «Генерация» |
| 2 | Вкладка «Сортировка» |
| 3 | Процесс / результат сортировки |
| 4 | Вкладка «Просмотр» |

## Сдача

PDF из `report/main.tex` + ссылка на репозиторий.
