import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import csv
import os
import subprocess
import time

from generator import DataGenerator
from external_sort import ExternalSort

class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Алкаши - Сортировка")
        self.root.geometry("950x650")
        self.col_names = ['ID', 'Фамилия', 'Имя', 'Факультет', 'Курс', 'Напиток',
                          'Бюджет', 'Стипендия', '% на алко', 'Где пьет', 'Похмелье',
                          'Прогулы', 'Отмазка', 'В кустах', 'Потерял', 'Статус',
                          'Драки', 'Признания', 'Звонки', 'Промилле', 'Кличка', 'Дата', 'Ср.Балл', 'Возвраст',
                          'Долги']

        self.generator = DataGenerator()
        self.build_ui()

    def build_ui(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=5, pady=5)

        tab1 = ttk.Frame(notebook)
        tab2 = ttk.Frame(notebook)
        tab3 = ttk.Frame(notebook)

        notebook.add(tab1, text='Генерация')
        notebook.add(tab2, text='Сортировка')
        notebook.add(tab3, text='Просмотр')

        self.build_gen_tab(tab1)
        self.build_sort_tab(tab2)
        self.build_view_tab(tab3)

    def build_gen_tab(self, parent):
        f = ttk.Frame(parent, padding=10)
        f.pack(fill='x')

        ttk.Label(f, text="Имя файла:").grid(row=0, column=0, sticky='w', pady=2)
        self.gen_file = tk.StringVar(value="alcoholics.csv")
        ttk.Entry(f, textvariable=self.gen_file, width=25).grid(row=0, column=1, pady=2)

        ttk.Button(f, text="Открыть справочник", command=self.open_dict).grid(row=0, column=2, padx=10, pady=2)

        ttk.Label(f, text="Ограничение по:").grid(row=1, column=0, sticky='w', pady=2)
        self.gen_mode = tk.StringVar(value="size")
        modes_frame = ttk.Frame(f)
        modes_frame.grid(row=1, column=1, sticky='w', pady=2)

        ttk.Radiobutton(modes_frame, text="Размеру (ГБ)", variable=self.gen_mode, value="size", command=self.toggle).pack(side='left')
        ttk.Radiobutton(modes_frame, text="Кол-ву строк", variable=self.gen_mode, value="rows", command=self.toggle).pack(side='left')

        # Создаем независимое поле для Размера (ГБ)
        self.lbl_size = ttk.Label(f, text="Размер ГБ:")
        self.lbl_size.grid(row=2, column=0, sticky='w', pady=2)
        self.gen_size = tk.StringVar(value="1.1")
        self.entry_size = ttk.Entry(f, textvariable=self.gen_size, width=15)
        self.entry_size.grid(row=2, column=1, sticky='w', pady=2)

        # Создаем независимое поле для Строк и сразу их прячем
        self.lbl_rows = ttk.Label(f, text="Кол-во строк:")
        self.lbl_rows.grid(row=2, column=0, sticky='w', pady=2)
        self.gen_rows = tk.StringVar(value="100000")
        self.entry_rows = ttk.Entry(f, textvariable=self.gen_rows, width=15)
        self.entry_rows.grid(row=2, column=1, sticky='w', pady=2)

        self.lbl_rows.grid_remove() # Физически скрываем надпись "строки"
        self.entry_rows.grid_remove() # Физически скрываем поле ввода "строки"

        ttk.Label(f, text="Кол-во файлов:").grid(row=3, column=0, sticky='w', pady=2)
        self.gen_count = tk.IntVar(value=1)
        ttk.Entry(f, textvariable=self.gen_count, width=15).grid(row=3, column=1, sticky='w', pady=2)

        ttk.Button(f, text="Генерировать", command=self.do_generate).grid(row=4, column=0, columnspan=2, pady=10)

        self.gen_status = tk.StringVar(value="Готов")
        ttk.Label(parent, textvariable=self.gen_status).pack()

        self.gen_log = tk.Text(parent, height=12)
        self.gen_log.pack(fill='both', expand=True, padx=10, pady=5)

    # Функция скрытия/показа нужных полей ввода
    def toggle(self):
        if self.gen_mode.get() == "size":
            self.lbl_rows.grid_remove()
            self.entry_rows.grid_remove()
            self.lbl_size.grid()
            self.entry_size.grid()
        else:
            self.lbl_size.grid_remove()
            self.entry_size.grid_remove()
            self.lbl_rows.grid()
            self.entry_rows.grid()

    # СОРТИРОВКА
    def build_sort_tab(self, parent):
        f = ttk.Frame(parent, padding=10)
        f.pack(fill='x')

        ttk.Label(f, text="Вход:").grid(row=0, column=0, sticky='w')
        self.sort_in = tk.StringVar(value="alcoholics.csv")
        ttk.Entry(f, textvariable=self.sort_in, width=25).grid(row=0, column=1)
        ttk.Button(f, text="...", command=self.browse_in, width=3).grid(row=0, column=2)

        ttk.Label(f, text="Выход:").grid(row=1, column=0, sticky='w')
        self.sort_out = tk.StringVar(value="sorted.csv")
        ttk.Entry(f, textvariable=self.sort_out, width=25).grid(row=1, column=1)

        ttk.Label(f, text="Столбец:").grid(row=2, column=0, sticky='w')
        self.sort_col_name = tk.StringVar(value='ID')
        self.col_combobox = ttk.Combobox(f, textvariable=self.sort_col_name, values=self.col_names, state="readonly", width=23)
        self.col_combobox.grid(row=2, column=1, sticky='w')

        ttk.Label(f, text="Порядок:").grid(row=3, column=0, sticky='w')
        self.sort_desc = tk.BooleanVar(value=False)
        order_frame = ttk.Frame(f)
        order_frame.grid(row=3, column=1, sticky='w')
        ttk.Radiobutton(order_frame, text="По возрастанию", variable=self.sort_desc, value=False).pack(side='left')
        ttk.Radiobutton(order_frame, text="По убыванию", variable=self.sort_desc, value=True).pack(side='left')

        ttk.Label(f, text="Язык:").grid(row=4, column=0, sticky='w')
        self.lang = tk.StringVar(value="Python")
        langs = ttk.Frame(f)
        langs.grid(row=4, column=1, sticky='w')
        ttk.Radiobutton(langs, text="Python", variable=self.lang, value="Python").pack(side='left')
        ttk.Radiobutton(langs, text="C++", variable=self.lang, value="C++").pack(side='left')

        ttk.Button(f, text="Сортировать", command=self.do_sort).grid(row=5, column=0, columnspan=3, pady=10)

        self.sort_status = tk.StringVar(value="Готов")
        ttk.Label(parent, textvariable=self.sort_status).pack()

        self.sort_log = tk.Text(parent, height=12)
        self.sort_log.pack(fill='both', expand=True, padx=10, pady=5)

    # ПРОСМОТР ТАБЛИЦЫ
    def build_view_tab(self, parent):
        f = ttk.Frame(parent, padding=10)
        f.pack(fill='x')

        ttk.Label(f, text="Файл:").pack(side='left')
        self.view_file = tk.StringVar(value="alcoholics.csv")
        ttk.Entry(f, textvariable=self.view_file, width=20).pack(side='left', padx=5)
        ttk.Button(f, text="...", command=self.browse_view, width=3).pack(side='left')

        ttk.Label(f, text="Строка:").pack(side='left', padx=(10, 0))
        self.view_start = tk.IntVar(value=0)
        ttk.Entry(f, textvariable=self.view_start, width=8).pack(side='left')

        ttk.Label(f, text="Кол-во:").pack(side='left', padx=(10, 0))
        self.view_count = tk.IntVar(value=50)
        ttk.Entry(f, textvariable=self.view_count, width=5).pack(side='left')

        self.btn_view = ttk.Button(f, text="Показать", command=self.do_view)
        self.btn_view.pack(side='left', padx=10)

        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # Добавлено 23-е поле 'avg_grade'
        cols = ('id', 'surname', 'name', 'faculty', 'course', 'favorite_drink',
                'alcohol_budget', 'stipendia', 'percent_on_alcohol', 'drinking_place',
                'morning_hangover', 'skipped_classes', 'favorite_excuse', 'slept_in_bushes',
                'lost_item', 'expulsion_status', 'drunk_fights', 'drunk_love_confessions',
                'drunk_calls_to_ex', 'max_promille', 'nickname', 'date', 'avg_grade', 'age', 'debt')

        sb_y = ttk.Scrollbar(tree_frame, orient='vertical')
        sb_x = ttk.Scrollbar(tree_frame, orient='horizontal')

        self.tree = ttk.Treeview(tree_frame, columns=cols, show='headings', height=15,
                                 yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)

        sb_y.config(command=self.tree.yview)
        sb_x.config(command=self.tree.xview)

        # Добавлена ширина 60 для последней колонки оценки
        widths = [50, 100, 100, 100, 50, 150, 80, 80, 80, 150, 80,
                  80, 150, 80, 120, 150, 60, 80, 60, 80, 120, 90, 60, 50,50]

        for i in range(len(cols)):
            self.tree.heading(cols[i], text=self.col_names[i])
            self.tree.column(cols[i], width=widths[i], minwidth=50, stretch=False)

        sb_y.pack(side='right', fill='y')
        sb_x.pack(side='bottom', fill='x')
        self.tree.pack(side='left', fill='both', expand=True)

    def log(self, widget, msg):
        def _log():
            widget.insert('end', msg + '\n')
            widget.see('end')
        self.root.after(0, _log)

    def update_status(self, string_var, msg):
        self.root.after(0, lambda: string_var.set(msg))

    def show_info(self, title, msg):
        self.root.after(0, lambda: messagebox.showinfo(title, msg))

    def show_error(self, title, msg):
        self.root.after(0, lambda: messagebox.showerror(title, msg))

    def browse_in(self):
        f = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if f: self.sort_in.set(f)

    def browse_view(self):
        f = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if f: self.view_file.set(f)

    def open_dict(self):
        if not os.path.exists("dictionary.txt"):
            messagebox.showinfo("Инфо", "Справочник еще не создан. Нажмите 'Генерировать', чтобы он появился.")
            return
        try:
            if os.name == 'nt':
                os.startfile("dictionary.txt")
            else:
                subprocess.call(['xdg-open', "dictionary.txt"])
        except Exception as e:
            self.show_error("Ошибка", f"Не удалось открыть файл: {e}")

    def do_generate(self):
        self.gen_log.delete('1.0', 'end')
        self.update_status(self.gen_status, "Генерация...")

        fname_base = self.gen_file.get()
        mode = self.gen_mode.get()
        count = self.gen_count.get()

        try:
            # Читаем значение из активного поля
            if mode == "size":
                limit_val = float(self.gen_size.get())
            else:
                limit_val = float(self.gen_rows.get())
        except ValueError:
            self.show_error("Ошибка", "Введите корректное число в активном поле!")
            return

        target_size_gb = limit_val if mode == "size" else None
        target_rows = int(limit_val) if mode == "rows" else None

        def work():
            try:
                total_records = 0
                name, ext = os.path.splitext(fname_base)
                if ext == "": ext = ".csv"

                for i in range(1, count + 1):
                    fname = fname_base if count == 1 else f"{name}_{i}{ext}"

                    self.log(self.gen_log, f"\n--- Генерация файла {i} из {count} ---")
                    if mode == "size":
                        self.log(self.gen_log, f"Цель: {target_size_gb} ГБ (Файл: {fname})")
                    else:
                        self.log(self.gen_log, f"Цель: {target_rows} строк (Файл: {fname})")

                    def make_callback(file_idx):
                        def callback(records, size_gb, progress):
                            self.update_status(self.gen_status, f"Файл {file_idx}/{count} | {progress:.1f}% | {records} зап.")
                        return callback

                    result_size, records = self.generator.generate_file(
                        fname, target_size_gb=target_size_gb, target_rows=target_rows, callback=make_callback(i)
                    )
                    total_records += records

                    self.log(self.gen_log, f"Файл {fname} готов! Записей: {records}, Вес: {result_size:.2f} ГБ")

                self.log(self.gen_log, f"\n=== ВСЕ ГОТОВО! Сгенерировано файлов: {count}, всего записей: {total_records} ===")
                self.update_status(self.gen_status, "Готово!")
                self.show_info("Готово", f"Сгенерировано файлов: {count}\nВсего записей: {total_records}")

            except Exception as e:
                self.log(self.gen_log, f"Ошибка: {e}")
                self.update_status(self.gen_status, "Ошибка!")
                self.show_error("Ошибка", str(e))

        threading.Thread(target=work, daemon=True).start()

    def do_sort(self):
        self.sort_log.delete('1.0', 'end')
        self.update_status(self.sort_status, "Сортировка...")

        inp = self.sort_in.get()
        out = self.sort_out.get()
        lang = self.lang.get()
        is_desc = self.sort_desc.get()
        order_text = "по убыванию" if is_desc else "по возрастанию"

        selected_col_name = self.sort_col_name.get()
        if selected_col_name in self.col_names:
            col_index = self.col_names.index(selected_col_name)
        else:
            col_index = 0

        def work():
            try:
                if not os.path.exists(inp):
                    raise Exception(f"Файл не найден: {inp}")

                self.log(self.sort_log, f"Язык: {lang}")
                self.log(self.sort_log, f"Столбец: {selected_col_name} (Индекс: {col_index}), {order_text}")

                if lang == "Python":
                    sorter = ExternalSort(memory_limit_mb=100)
                    try:
                        s, m, t = sorter.sort(inp, out, col_index, reverse=is_desc)
                        self.log(self.sort_log, f"Разбиение: {s:.1f} сек")
                        self.log(self.sort_log, f"Слияние: {m:.1f} сек")
                        self.log(self.sort_log, f"Всего: {t:.1f} сек")
                    finally:
                        if hasattr(sorter, 'cleanup'): sorter.cleanup()

                else:
                    self.log(self.sort_log, "Компиляция C++...")

                    exe_name = f"external_sort_{int(time.time())}.exe" if os.name == "nt" else f"external_sort_{int(time.time())}"

                    r = subprocess.run(
                        ['g++', '-std=c++17', '-O2', 'external_sort.cpp', '-o', exe_name],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='ignore'
                    )

                    if r.returncode != 0:
                        err_msg = r.stderr if r.stderr else "Неизвестная ошибка компиляции"
                        raise Exception(f"Ошибка компиляции: {err_msg}")

                    self.log(self.sort_log, "Запуск программы...")

                    exe_run_cmd = f".\\{exe_name}" if os.name == "nt" else f"./{exe_name}"

                    r2 = subprocess.run(
                        [exe_run_cmd, inp, out, str(col_index), "1" if is_desc else "0"],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='ignore'
                    )

                    try:
                        if os.path.exists(exe_name):
                            os.remove(exe_name)
                    except:
                        pass

                    out_str = r2.stdout if r2.stdout else ""
                    for line in out_str.split('\n'):
                        if line.strip():
                            self.log(self.sort_log, line.strip())

                    if r2.returncode != 0:
                        raise Exception(f"Ошибка выполнения C++: {r2.stderr}")

                self.update_status(self.sort_status, "Готово!")
                self.show_info("Готово", f"Файл отсортирован: {out}")

            except Exception as e:
                self.log(self.sort_log, f"Ошибка: {e}")
                self.update_status(self.sort_status, "Ошибка!")
                self.show_error("Ошибка", str(e))

        threading.Thread(target=work, daemon=True).start()

    def do_view(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        fname = self.view_file.get()
        start = self.view_start.get()
        count = self.view_count.get()

        if not os.path.exists(fname):
            messagebox.showerror("Ошибка", f"Файл не найден: {fname}")
            return

        if count > 5000:
            messagebox.showwarning("Внимание", "Лимит 5000 строк для отображения.")
            count = 5000
            self.view_count.set(5000)

        self.btn_view.config(state='disabled')
        self.root.title("Алкаши - Сортировка (Загрузка...)")

        def work():
            try:
                rows_to_show = []
                with open(fname, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    try:
                        next(reader)
                    except StopIteration:
                        pass

                    for _ in range(start):
                        try:
                            next(reader)
                        except StopIteration:
                            break

                    loaded = 0
                    for row in reader:
                        if loaded >= count:
                            break
                        if len(row) > 0:
                            # Лимит поднят до 25 ЧТОБЫ РАБОТАЛООООООООООЛООЛЛОЛОЛОЛО
                            while len(row) < 25:
                                row.append("")

                            rows_to_show.append(row[:25])
                            loaded += 1

                def update_tree():
                    for r in rows_to_show:
                        self.tree.insert('', 'end', values=r)
                    self.btn_view.config(state='normal')
                    self.root.title("Алкаши - Сортировка")

                self.root.after(0, update_tree)

            except Exception as e:
                self.show_error("Ошибка", str(e))
                self.root.after(0, lambda: self.btn_view.config(state='normal'))
                self.root.after(0, lambda: self.root.title("Алкаши - Сортировка"))

        threading.Thread(target=work, daemon=True).start()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = App()
    app.run()