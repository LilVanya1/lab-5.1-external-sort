import random
import time
import os

class DataGenerator:
    def __init__(self):
        self.dict_file = "dictionary.txt"
        self.last_mtime = 0

        self.surnames = []
        self.names = []
        self.faculties = []
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
        content = """[Фамилии]
Пивнов
Бухалов
Водкин
Перегаров
Похмелюк
Бодунов
Застольный

[Имена]
Вася
Петя
Серёга
Димон
Колян
Олег

[Факультеты]
Физмат
Филфак
Журфак
Экономика
ПМИ

[Напитки]
пиво разливное
пиво баночное
водка
самогон от бабушки
винишко дешёвое

[Места]
общага комната
общага кухня
парк у универа
за гаражами
на паре

[Отмазки]
болел
бабушка умерла
пробки
проспал
будильник сломался

[Статусы]
пока держится
на грани
академка
отчислен но ходит

[Потери]
телефон
ключи
зачётку
студенческий
достоинство
всё

[Клички]
Печень
Два пива
Синий
На посошок
Трезвый
"""
        with open(self.dict_file, 'w', encoding='utf-8') as f:
            f.write(content)

    def _load_dict(self):
        temp_dict = {
            '[Фамилии]': [], '[Имена]': [], '[Факультеты]': [],
            '[Напитки]': [], '[Места]': [], '[Отмазки]': [],
            '[Статусы]': [], '[Потери]': [], '[Клички]': []
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

            self.surnames = temp_dict['[Фамилии]'] or ['Нет данных']
            self.names = temp_dict['[Имена]'] or ['Нет данных']
            self.faculties = temp_dict['[Факультеты]'] or ['Нет данных']
            self.drinks = temp_dict['[Напитки]'] or ['Нет данных']
            self.places = temp_dict['[Места]'] or ['Нет данных']
            self.excuses = temp_dict['[Отмазки]'] or ['Нет данных']
            self.statuses = temp_dict['[Статусы]'] or ['Нет данных']
            self.lost_items = temp_dict['[Потери]'] or ['Нет данных']
            self.nicknames = temp_dict['[Клички]'] or ['Нет данных']

            self.last_mtime = os.path.getmtime(self.dict_file)
        except Exception:
            pass

            # Добавлено 23-е поле 'avg_grade' в системный заголовок CSV
    def get_header(self):
        return [
            'id', 'surname', 'name', 'faculty', 'course', 'favorite_drink',
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

                surnames, names, faculties = self.surnames, self.names, self.faculties
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
                    row = f"{record_id},{rc(surnames)},{rc(names)},{rc(faculties)},{ri(1, 6)},{rc(drinks)},{budg},{stip},{perc},{rc(places)},{rc(yes_no)},{ri(0, 200)},{rc(excuses)},{ri(0, 50)},{rc(lost_items)},{rc(statuses)},{ri(0, 20)},{ri(0, 100)},{ri(0, 500)},{round(ru(0.5, 4.2), 1)},{rc(nicknames)},{date_str},{round(ru(1.0, 5.0), 1)},{ri(18, 65)},{ri(0,30)}\n"

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