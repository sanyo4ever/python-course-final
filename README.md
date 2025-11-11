# Personal Assistant CLI

Командний фінальний проєкт курсу **Python Programming: Foundations and Best Practices**. Застосунок надає інтерфейс командного рядка для керування контактами та нотатками із повною підтримкою збереження даних на диску.

## Можливості

- зберігання контактів з іменами, телефонами, адресами, email та днями народження;
- валідація номерів телефонів і електронних адрес;
- пошук, редагування й видалення контактів;
- відображення контактів із днями народження впродовж заданої кількості днів;
- створення, редагування, пошук і видалення нотаток;
- додавання тегів до нотаток, пошук і сортування за тегами;
- підказка найближчої команди за некоректного введення;
- збереження даних у каталозі користувача (`~/.personal_assistant`).

## Встановлення

> Потрібен Python 3.10 або новіший.

1. Клонуйте репозиторій:

   ```bash
   git clone https://github.com/your-team/personal-assistant-cli.git
   cd personal-assistant-cli
   ```

2. Встановіть пакет у поточне середовище:

   ```bash
   pip install .
   ```

   або в режимі розробки:

   ```bash
   pip install -e .
   ```

## Запуск

Після встановлення команда `personal-assistant` доступна будь-де в системі:

```bash
personal-assistant
```

Перший запуск створить директорію `~/.personal_assistant` для збереження контактів та нотаток.

## Використання

Асистент працює в інтерактивному режимі. Основні команди:

- `add contact John phone=+380501112233 email=john@example.com address="Kyiv" birthday=1990-05-12`
- `list contacts`
- `show contact John`
- `edit contact John phone=+380501112233:+380671112233 email=johnny@example.com`
- `delete contact John`
- `search contacts John`
- `upcoming birthdays 7`
- `add note Roadmap content="Discuss features" tags=work,planning`
- `list notes`
- `show note Roadmap`
- `edit note Roadmap content="Updated text" add_tags=urgent remove_tags=planning`
- `delete note Roadmap`
- `search notes roadmap`
- `search notes by tag work`
- `sort notes by tags`
- `exit` / `quit`

У будь-який момент можна ввести `help` або `commands`, щоб побачити повний список і приклади.

## Структура проєкту

```
src/personal_assistant/
├── __init__.py       # Експортує ключові класи та функцію main
├── address_book.py   # Книга контактів
├── cli.py            # Інтерактивний CLI-інтерфейс
├── commands.py       # Реалізація команд
├── fields.py         # Класи полів із валідацією
├── notes.py          # Модулі нотаток і тегів
├── record.py         # Окремий запис контакту
└── storage.py        # Збереження/завантаження даних
```

## Розробка

- Код відповідає стандартам PEP 8.
- Для запуску лінтера (наприклад, `ruff`) та тестів рекомендується налаштувати власні скрипти у віртуальному середовищі.
- Будь-які зміни супроводжуйте оновленням документації в `README.md`.

## Ліцензія

Проєкт ліцензовано за умовами MIT License.


