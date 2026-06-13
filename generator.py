import random
import time
import os

class DataGenerator:
    def __init__(self):
        self.dict_file = "dictionary.txt"
        self.last_mtime = 0

        self.store_names = []  # полные названия из [Название 1] в dictionary.txt
        self.districts = []
        self.drinks = []
        self.places = []
        self.excuses = []
        self.statuses = []
        self.lost_items = []
        self.nicknames = []
        self.age = []
        self.debt = []

        self.years = [str(y) for y in range(2015, 2024)]
        self.months = [f"{m:02d}" for m in range(1, 13)]
        self.days = [f"{d:02d}" for d in range(1, 29)]

        if not os.path.exists(self.dict_file):
            self._create_default_dict()

        self._load_dict()

    def _create_default_dict(self):
        content = """[Название 1]
Пивной угол
Бочка у рынка
Кран 24/7
Балтика у дома
Жигуль на остановке
Разлив во дворе

[Районы]
Центр
Север
Юг
Спальный
Промзона
У ТЦ

[Напитки]
пиво разливное
пиво баночное
сидр
медовуха
вода газированная
снеки

[Расположения]
первый этаж
подъезд
ТЦ проход
рынок ряд
у метро
отдельный павильон

[Причины]
поставка задержалась
пересорт
проверка Росалкоголь
отключили свет
касса сломалась
нехватка сдачи

[Статусы]
действует
на проверке
временно закрыт
лицензия истекает
новый владелец
реконструкция

[Потери]
товар
выручка за смену
холодильник
лицензия
касса
витрина

[Вывески]
Дёшево
24 часа
Пиво здесь
Скидки
Свежая разливуха
Уголок
"""
        with open(self.dict_file, 'w', encoding='utf-8') as f:
            f.write(content)

    def _load_dict(self):
        temp_dict = {
            '[Название 1]': [], '[Районы]': [],
            '[Напитки]': [], '[Расположения]': [], '[Причины]': [],
            '[Статусы]': [], '[Потери]': [], '[Вывески]': [],
            # совместимость со старым dictionary.txt
            '[Фамилии]': [], '[Имена]': [], '[Факультеты]': [],
            '[Места]': [], '[Отмазки]': [], '[Клички]': [],
        }

        try:
            with open(self.dict_file, 'r', encoding='utf-8') as f:
                current_category = None
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith('[') and line.endswith(']'):
                        current_category = line
                    elif current_category in temp_dict:
                        temp_dict[current_category].append(line)

            self.store_names = (
                temp_dict['[Название 1]'] or temp_dict['[Фамилии]'] or ['Нет данных']
            )
            self.districts = (
                temp_dict['[Районы]'] or temp_dict['[Факультеты]'] or ['Нет данных']
            )
            self.drinks = temp_dict['[Напитки]'] or ['Нет данных']
            self.places = (
                temp_dict['[Расположения]'] or temp_dict['[Места]'] or ['Нет данных']
            )
            self.excuses = (
                temp_dict['[Причины]'] or temp_dict['[Отмазки]'] or ['Нет данных']
            )
            self.statuses = temp_dict['[Статусы]'] or ['Нет данных']
            self.lost_items = temp_dict['[Потери]'] or ['Нет данных']
            self.nicknames = (
                temp_dict['[Вывески]'] or temp_dict['[Клички]'] or ['Нет данных']
            )

            self.last_mtime = os.path.getmtime(self.dict_file)
        except Exception:
            pass

            # Добавлено 23-е поле 'avg_grade' в системный заголовок CSV
    def get_header(self):
        return [
            'id', 'surname', 'faculty', 'course', 'favorite_drink',
            'alcohol_budget', 'stipendia', 'percent_on_alcohol', 'drinking_place',
            'morning_hangover', 'skipped_classes', 'favorite_excuse', 'slept_in_bushes',
            'lost_item', 'expulsion_status', 'drunk_fights', 'drunk_love_confessions',
            'drunk_calls_to_ex', 'max_promille', 'nickname', 'date', 'avg_grade', 'age', 'debt'
        ]

    def generate_file(self, filename, target_size_gb=None, target_rows=None, callback=None):
        if target_size_gb:
            target_size = int(target_size_gb * 1024 * 1024 * 1024)
        else:
            target_size = None

        rc = random.choice
        ri = random.randint
        ru = random.uniform

        record_id = 1
        start_time = time.time()

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(','.join(self.get_header()) + '\n')

            while True:
                try:
                    current_mtime = os.path.getmtime(self.dict_file)
                    if current_mtime != self.last_mtime:
                        self._load_dict()
                except Exception:
                    pass

                names, faculties = self.store_names, self.districts
                drinks, places, excuses = self.drinks, self.places, self.excuses
                statuses, lost_items, nicknames = self.statuses, self.lost_items, self.nicknames
                years, months, days = self.years, self.months, self.days
                yes_no = ['да', 'нет']

                batch = []

                if target_rows:
                    batch_size = min(100000, target_rows - (record_id - 1))
                    if batch_size <= 0:
                        break
                else:
                    batch_size = 100000

                for _ in range(batch_size):
                    stip = ri(0, 5000)
                    budg = ri(500, 15000)
                    perc = min(int(budg / stip * 100), 300) if stip > 0 else 0
                    date_str = f"{rc(years)}-{rc(months)}-{rc(days)}"

                    # Добавлена генерация float значения оценки (ru(1.0, 5.0)) в самый конец строки перед \n
                    row = f"{record_id},{rc(names)},{rc(faculties)},{ri(1, 6)},{rc(drinks)},{budg},{stip},{perc},{rc(places)},{rc(yes_no)},{ri(0, 200)},{rc(excuses)},{ri(0, 50)},{rc(lost_items)},{rc(statuses)},{ri(0, 20)},{ri(0, 100)},{ri(0, 500)},{round(ru(0.5, 4.2), 1)},{rc(nicknames)},{date_str},{round(ru(1.0, 5.0), 1)},{ri(18, 65)},{ri(0,30)}\n"

                    batch.append(row)
                    record_id += 1

                f.writelines(batch)
                current_size = f.tell()

                if target_size:
                    progress = min(current_size / target_size * 100, 100.0)
                else:
                    progress = min((record_id - 1) / target_rows * 100, 100.0)

                size_gb = current_size / (1024 ** 3)

                if callback:
                    callback(record_id - 1, size_gb, progress)

                if target_size and current_size >= target_size:
                    break
                if target_rows and (record_id - 1) >= target_rows:
                    break

        final_size = current_size / (1024 ** 3)
        return final_size, record_id - 1