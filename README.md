# Социальная сеть блогеров

## Описание
Социальная сеть с сообществами для публикации дневниковых записей.

В проекте реализованы:
- регистрация и аутентификация пользователей на основе JWT-токенов;
- сообщества (группы);
- подписки на авторов;
- комментарии к постам;
- загрузка картинок;
- пагинация;
- кэширование.

Проект покрыт тестами (Unittest).

Также см. [REST API](https://github.com/ArnoSimonian/social_blog_network_api) для этого проекта на DRF.

## Технологии

- Python 3.7
- Django 2.2.19
- Simple JWT
- SQLite 3
- HTML5
- CSS
- Bootstrap
- Unittest


## Запуск проекта в dev-режиме

1. Cоздайте и активируйте виртуальное окружение:

```bash
  python3 -m venv venv
  # Для Linux/macOS:
  source venv/bin/activate
  # Для Windows:
  source venv/Scripts/activate
```

2. Установите зависимости из файла requirements.txt:

```bash
  python3 -m pip install --upgrade pip
  pip install -r requirements.txt
```

3. Выполните миграции и запустите проект:

```bash
  python3 manage.py migrate
  python3 manage.py runserver
```


## Автор

Арно Симонян [@ArnoSimonian](https://www.github.com/ArnoSimonian)
