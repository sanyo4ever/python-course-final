# Детальний опис функціоналу Personal Assistant CLI

## Огляд архітектури

Personal Assistant CLI — це модульний застосунок командного рядка для управління контактами та нотатками з повною персистентністю даних. Архітектура базується на принципах чистого коду, розділення відповідальностей та валідації даних.

---

## Модульна структура

### 1. `cli.py` — Інтерфейс командного рядка

**Клас:** `PersonalAssistantCLI`

**Відповідальність:**
- Головний цикл введення/виведення (REPL)
- Парсинг команд користувача
- Делегування обробки до відповідних хендлерів
- Відображення результатів та помилок

**Ключові особливості:**
- Реєстр команд (`CommandRegistry`) з підтримкою пріоритету (довші команди першими)
- Обробка `EOFError` та `KeyboardInterrupt` для graceful shutdown
- Інтеграція з системою підказок при невідомих командах
- Автоматичне завантаження даних при старті

**Алгоритм розпізнавання команд:**
```python
# Команди сортуються за довжиною (від найдовших до найкоротших)
# Це дозволяє коректно розпізнавати "search notes by tag" перед "search notes"
for command_name in sorted(commands, key=len, reverse=True):
    if user_input.lower().startswith(command_name):
        return handler, arguments
```

---

### 2. `commands.py` — Бізнес-логіка команд

**Основні компоненти:**

#### `AppContext` (dataclass)
Контейнер для спільного стану застосунку:
- `address_book: AddressBook` — книга контактів
- `notebook: Notebook` — блокнот нотаток
- `storage: Storage` — система збереження

#### `CommandResult` (dataclass)
Уніфікована структура відповіді команди:
- `message: str` — текст для виведення користувачу
- `should_exit: bool` — чи треба завершити роботу

#### Функції-команди

Всі команди мають сигнатуру: `(AppContext, str) -> CommandResult`

**Групи команд:**

##### Контакти
1. **`add_contact`** — створення нового контакту
   - Парсинг аргументів через `shlex.split` (підтримка лапок)
   - Витягування пар ключ=значення
   - Множинні телефони через `phone1=...`, `phone2=...`
   - Валідація через конструктор `ContactRecord`
   - Автоматичне збереження після додавання

2. **`list_contacts`** — виведення всіх контактів
   - Повна інформація по кожному контакту
   - Форматоване виведення

3. **`show_contact`** — деталі одного контакту
   - Пошук без врахування регістру
   - Повідомлення про помилку, якщо не знайдено

4. **`edit_contact`** — редагування існуючого контакту
   - Підтримка оновлення телефонів (формат `phone=old:new`)
   - Додавання нових телефонів
   - Оновлення email, адреси, дня народження
   - Перехоплення `ValidationError`

5. **`delete_contact`** — видалення контакту
   - Перевірка існування
   - Автоматичне збереження

6. **`search_contacts`** — пошук по всіх полях
   - Кейс-інсенсітивний пошук
   - Пошук у імені, телефонах, email, адресі
   - Виведення всіх збігів

7. **`upcoming_birthdays`** — пошук днів народження
   - Обчислення днів до наступного дня народження
   - Фільтрація по кількості днів вперед
   - Сортування та форматоване виведення

##### Нотатки
1. **`add_note`** — створення нової нотатки
   - Парсинг заголовку, вмісту та тегів
   - Теги розділяються комами
   - Автоматичне нормалізування тегів (lower case)

2. **`list_notes`** — список всіх нотаток
   - Виведення заголовків зі списком тегів

3. **`show_note`** — повний вміст нотатки
   - Заголовок, теги та текст

4. **`edit_note`** — редагування нотатки
   - Оновлення вмісту (`content=...`)
   - Додавання тегів (`add_tags=...`)
   - Видалення тегів (`remove_tags=...`)
   - Можливість комбінованих операцій

5. **`delete_note`** — видалення нотатки

6. **`search_notes`** — пошук по вмісту
   - Пошук у заголовку, вмісті та тегах

7. **`search_notes_by_tag`** — фільтрація за тегом
   - Точний збіг тегу

8. **`sort_notes_by_tags`** — сортування нотаток
   - Спочатку по тегах (алфавітно)
   - Потім по заголовку

##### Системні
- **`exit_command`** / **`quit`** — вихід з CLI

#### Допоміжні функції

**`parse_key_value_args(argument_string: str) -> Dict[str, str]`**
- Парсинг аргументів формату `key=value`
- Використання `shlex.split` для підтримки лапок
- Нормалізація ключів до lower case

**`require_name(argument_string: str) -> str`**
- Валідація обов'язкового параметру імені
- Викидає `CommandError` якщо порожній

**`suggest_command(user_input: str, command_map) -> Optional[str]`**
- Використання `difflib.get_close_matches`
- Поріг схожості 0.5
- Повертає найближчий варіант

---

### 3. `fields.py` — Валідовані поля

**Базовий клас:** `Field`

**Патерн дизайну:** Дескриптор з валідацією

**Архітектура валідації:**
```python
@property
def value(self):
    return self._value

@value.setter
def value(self, value):
    self._value = self.validate(value)  # Валідація при присвоєнні
```

#### Класи полів

1. **`Name`**
   - Валідація: не порожнє після strip()
   - Помилка: `"Name cannot be empty."`

2. **`Phone`**
   - Регулярний вираз: `^\+?\d{7,15}$`
   - Видалення пробілів
   - Перевірка на 7-15 цифр
   - Опціональний '+' на початку
   - Помилка: `"Phone number must contain 7-15 digits and may start with '+'."`

3. **`Email`**
   - Регулярний вираз: `^(?=.{3,254}$)(?!.*\.\.)[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$`
   - Перевірка загальної довжини (3-254 символи)
   - Заборона подвійних крапок
   - Стандартний email-формат
   - Помилка: `"Invalid email format."`

4. **`Address`**
   - Валідація: не порожня після strip()
   - Помилка: `"Address cannot be empty."`

5. **`Birthday`**
   - Формат: `YYYY-MM-DD`
   - Підтримка `str` та `datetime` на вході
   - Конвертація до `datetime` об'єкта
   - Форматоване виведення через `__str__`
   - Помилка: `"Birthday must be in YYYY-MM-DD format."`

**`ValidationError`**
- Кастомне виключення, успадковане від `ValueError`
- Використовується для всіх помилок валідації

---

### 4. `record.py` — Запис контакту

**Клас:** `ContactRecord`

**Структура:**
```python
name: Name                    # Обов'язкове, унікальне
phones: List[Phone]          # 0 або більше
email: Optional[Email]       # 0 або 1
address: Optional[Address]   # 0 або 1
birthday: Optional[Birthday] # 0 або 1
```

**Методи управління телефонами:**

1. **`add_phone(phone: str)`** — додає новий телефон до списку
2. **`remove_phone(phone: str) -> bool`** — видаляє по значенню
3. **`edit_phone(old: str, new: str) -> bool`** — замінює існуючий

**Методи оновлення:**

- `set_email(email: str | None)` — встановлює або очищає email
- `set_address(address: str | None)` — встановлює або очищає адресу
- `set_birthday(birthday: str | datetime | None)` — встановлює або очищає день народження

**Бізнес-логіка:**

**`days_to_birthday(today: datetime | None) -> Optional[int]`**
```python
# Алгоритм:
1. Якщо немає дня народження → None
2. Перенести день народження на поточний рік
3. Якщо вже минув → перенести на наступний рік
4. Повернути різницю в днях
```

**`matches(query: str) -> bool`**
- Пошук підрядка у всіх текстових полях
- Кейс-інсенсітивний
- Повертає `True` при будь-якому збігу

**Серіалізація:**

- **`to_dict() -> Dict[str, Any]`** — конвертує у JSON-сумісний словник
- **`from_dict(data: Dict[str, Any]) -> ContactRecord`** (class method) — відновлює з словника

**Відображення:**

`__str__` форматує запис у читабельний рядок:
```
John Doe | Phones: +380501234567, +380671112233 | Email: john@example.com | Address: Kyiv | Birthday: 1990-01-15
```

---

### 5. `address_book.py` — Книга контактів

**Клас:** `AddressBook(UserDict[str, ContactRecord])`

**Патерн дизайну:** Wrapper над словником з додатковою логікою

**Ключова особливість:** Ключі нормалізуються до lower case для case-insensitive пошуку

**Методи CRUD:**

1. **`add_record(record: ContactRecord)`**
   - Ключ: `record.name.value.lower()`
   - Перезаписує, якщо існує

2. **`get(name: str) -> Optional[ContactRecord]`**
   - Case-insensitive пошук
   - Повертає `None` якщо не знайдено

3. **`remove(name: str) -> bool`**
   - Видаляє по імені
   - Повертає `True` якщо видалено

**Пошук та фільтрація:**

1. **`search(query: str) -> List[ContactRecord]`**
   - Використовує `record.matches(query)`
   - Збирає всі записи зі збігами

2. **`upcoming_birthdays(days_ahead: int, today: datetime | None) -> List[ContactRecord]`**
   - Обчислює `days_to_birthday` для кожного запису
   - Фільтрує діапазон `0 <= days <= days_ahead`
   - Параметр `today` для тестування

**Конвертація:**

- **`to_list() -> List[ContactRecord]`** — усі записи як список
- **`to_serializable() -> List[Dict[str, str]]`** — для JSON
- **`from_serializable(data) -> AddressBook`** (class method) — відновлення з JSON

---

### 6. `notes.py` — Нотатки та блокнот

#### Клас `Note` (dataclass)

**Поля:**
```python
title: str                 # Заголовок (використовується як ключ)
content: str               # Текст нотатки
tags: Set[str]            # Множина тегів (lower case)
```

**Методи управління тегами:**

1. **`add_tags(new_tags: Iterable[str])`**
   - Нормалізація: `strip()` + `lower()`
   - Фільтрація порожніх
   - Додавання до множини (автоматична дедуплікація)

2. **`remove_tag(tag: str) -> bool`**
   - Видалення одного тегу
   - Повертає `True` якщо знайдено

**Пошук:**

**`matches(query: str) -> bool`**
- Пошук у заголовку
- Пошук у вмісті
- Пошук у тегах (часткове співпадіння)
- Case-insensitive

**Серіалізація:**

- `to_dict()` — теги сортуються для консистентності
- `from_dict(data)` — відновлює з словника

#### Клас `Notebook(UserDict[str, Note])`

**Патерн:** Аналогічно `AddressBook`

**Ключі:** `note.title.lower()` для case-insensitive доступу

**Методи CRUD:**

1. **`add(note: Note)`** — додає або оновлює нотатку
2. **`get(title: str) -> Optional[Note]`** — отримує по заголовку
3. **`remove(title: str) -> bool`** — видаляє по заголовку

**Пошук:**

1. **`search(query: str) -> List[Note]`**
   - Використовує `note.matches(query)`
   - Повертає всі збіги

2. **`search_by_tag(tag: str) -> List[Note]`**
   - Точний збіг тегу (після нормалізації)
   - Сортування по заголовку

**Сортування:**

**`sorted_by_tags() -> List[Note]`**
```python
# Ключ сортування:
1. Відсортовані теги (алфавітно)
2. Заголовок (алфавітно)
# Нотатки без тегів йдуть першими
```

**Серіалізація:**

- `to_serializable() -> List[dict]` — для JSON
- `from_serializable(data) -> Notebook` — відновлення з JSON

---

### 7. `storage.py` — Персистентність даних

**Клас:** `Storage`

**Конфігурація:**
```python
DEFAULT_STORAGE_DIR = Path.home() / ".personal_assistant"
CONTACTS_FILE = "contacts.json"
NOTES_FILE = "notes.json"
```

**Структура файлів:**
```
~/.personal_assistant/
├── contacts.json
└── notes.json
```

**Методи:**

1. **`__init__(base_dir: Path | None)`**
   - Створює директорію, якщо не існує
   - `mkdir(parents=True, exist_ok=True)`

2. **`load() -> Tuple[AddressBook, Notebook]`**
   - Зчитує JSON файли
   - Парсить через `from_serializable`
   - Якщо файли не існують — повертає порожні контейнери
   - Кодування: UTF-8 для підтримки Unicode

3. **`save(address_book: AddressBook, notebook: Notebook)`**
   - Серіалізує через `to_serializable()`
   - Записує JSON з відступами (`indent=2`)
   - `ensure_ascii=False` для читабельності Unicode
   - Атомарний запис (Python автоматично)

**Формат JSON:**

**contacts.json:**
```json
[
  {
    "name": "Alice",
    "phones": ["+380501234567"],
    "email": "alice@example.com",
    "address": null,
    "birthday": "1990-03-15"
  }
]
```

**notes.json:**
```json
[
  {
    "title": "Meeting Notes",
    "content": "Discussed roadmap",
    "tags": ["planning", "work"]
  }
]
```

---

## Ключові алгоритми та патерни

### 1. Розпізнавання команд

**Проблема:** команди можуть бути префіксами інших (`"search notes"` vs `"search notes by tag"`)

**Рішення:**
```python
# Сортування за довжиною (спадання)
sorted(command_map.keys(), key=len, reverse=True)

# Перевірка префіксу
if user_input.lower().startswith(command_name):
    arguments = user_input[len(command_name):].strip()
```

**Результат:** довші команди мають пріоритет

### 2. Парсинг аргументів

**Використання `shlex.split`:**
- Підтримка лапок (`"Kyiv, Shevchenko St."`)
- Екранування спецсимволів
- Розбиття по пробілах з врахуванням лапок

**Парсинг key=value:**
```python
for token in shlex.split(argument_string):
    if "=" in token:
        key, value = token.split("=", maxsplit=1)
        pairs[key.lower()] = value.strip()
```

### 3. Обчислення днів до дня народження

```python
def days_to_birthday(self, today: datetime | None) -> Optional[int]:
    if not self.birthday:
        return None
    today = today or datetime.today()
    
    # Переносимо день народження на поточний рік
    birthday_this_year = self.birthday.value.replace(year=today.year)
    
    # Якщо вже минув — беремо наступний рік
    if birthday_this_year < today:
        birthday_this_year = birthday_this_year.replace(year=today.year + 1)
    
    return (birthday_this_year - today).days
```

**Обробка крайніх випадків:**
- Сьогодні день народження → 0 днів
- Вчора був → ~365 днів
- 29 лютого (не розглядається)

### 4. Case-insensitive пошук

**Патерн:**
```python
# Нормалізація ключів при збереженні
self.data[record.name.value.lower()] = record

# Нормалізація при пошуку
def get(self, name: str):
    return self.data.get(name.lower())
```

**Переваги:**
- Користувач може вводити будь-яким регістром
- Уникнення дублікатів

### 5. Автоматичне збереження

**Патерн:**
```python
def edit_contact(context: AppContext, arguments: str):
    # ... модифікація даних ...
    context.storage.save(context.address_book, context.notebook)
    return CommandResult("Updated")
```

**Особливості:**
- Збереження після кожної зміни
- Гарантія консистентності
- Простота відновлення після збою

---

## Обробка помилок

### Ієрархія виключень

1. **`ValidationError`** (успадковано від `ValueError`)
   - Викидається полями при невалідних даних
   - Перехоплюється в командах
   - Конвертується у `CommandError`

2. **`CommandError`** (успадковано від `Exception`)
   - Доменна помилка рівня команди
   - Перехоплюється в CLI
   - Виводиться як "Error: <message>"

3. **Загальні виключення**
   - Ловляться як `Exception` з позначкою "Unexpected error"

### Graceful degradation

```python
try:
    result = handler(context, arguments)
except CommandError as error:
    print(f"Error: {error}")
    continue  # Не виходимо з циклу
except Exception as error:
    print(f"Unexpected error: {error}")
    continue
```

---

## Тестування та якість коду

### Інжектовані залежності

**`Storage` приймає `base_dir`:**
```python
# У тестах
test_storage = Storage(base_dir=tmp_path)

# У production
default_storage = Storage()  # Використає ~/.personal_assistant
```

**Параметр `today` у методах днів народження:**
```python
# Дозволяє тестувати з фіксованою датою
record.days_to_birthday(today=datetime(2024, 1, 1))
```

### Принципи чистого коду

1. **Single Responsibility:** кожен модуль має одну відповідальність
2. **Dependency Injection:** залежності передаються ззовні
3. **Type Hints:** повна типізація для кращої документації
4. **Dataclasses:** мінімум boilerplate коду
5. **Immutability:** де можливо (наприклад, `CommandResult`)

### PEP 8 та стиль

- Використання `ruff` або `black` для форматування
- Docstrings для класів
- Імпорти з `__future__` для сумісності
- Type hints з `from typing import`

---

## Розширюваність

### Додавання нової команди

1. Написати функцію-хендлер:
```python
def my_command(context: AppContext, arguments: str) -> CommandResult:
    # Логіка
    return CommandResult("Done")
```

2. Додати у `build_command_map()`:
```python
"my command": (my_command, "Description of my command"),
```

3. Готово! CLI автоматично розпізнає команду.

### Додавання нового поля до контакту

1. Створити новий клас у `fields.py`:
```python
class Website(Field):
    def validate(self, value: str) -> str:
        # Валідація URL
        return value
```

2. Додати поле до `ContactRecord`:
```python
self.website: Website | None = Website(website) if website else None
```

3. Оновити `to_dict` та `from_dict`

4. Додати обробку в `edit_contact`

---

## Обмеження та майбутні покращення

### Поточні обмеження

1. **Немає конкурентного доступу** — якщо два процеси пишуть одночасно, можлива втрата даних
2. **Немає індексів** — пошук O(n) по всіх записах
3. **Немає пагінації** — при великій кількості записів виводиться все
4. **Немає бекапів** — користувач має самостійно робити копії JSON
5. **Немає автокомплітів** — треба друкувати команди повністю

### Можливі покращення

1. **SQLite замість JSON** — для швидшого пошуку та транзакцій
2. **Readline автокомпліт** — підказки при вводі команд
3. **Експорт/імпорт** — CSV, vCard для контактів
4. **Історія команд** — можливість повторити попередню команду
5. **Бекап при зміні** — автоматичне створення `.bak` файлів
6. **Багатомовність** — переклади інтерфейсу
7. **Кольоровий вивід** — для кращого UX
8. **Інтеграція з календарем** — нагадування про дні народження
9. **Web API** — для інтеграції з іншими застосунками
10. **Шифрування** — для захисту персональних даних

---

## Висновок

Personal Assistant CLI демонструє:
- ✅ Модульну архітектуру з чітким розділенням відповідальностей
- ✅ Надійну валідацію даних на всіх рівнях
- ✅ Персистентність через JSON з підтримкою Unicode
- ✅ Гнучкий інтерфейс команд з інтелектуальними підказками
- ✅ Розширюваність через інжекцію залежностей
- ✅ Чистий код з повною типізацією

Це повнофункціональний застосунок, готовий до використання та подальшого розвитку.

