# homework_bot
python telegram bot
# hw05_final

[![CI](https://github.com/yandex-praktikum/hw04_tests/actions/workflows/python-app.yml/badge.svg?branch=master)](https://github.com/yandex-praktikum/hw04_tests/actions/workflows/python-app.yml)


# Как запустить проект: Python, Django

# Установка Клонируйте репозиторий:

git clone https://github.com/AlexAvdeev1986/hw05_final.git

# Активация виртуального окружения:

python3 -m venv venv

source venv/bin/activate 

# Обновление пакетов:

python3 -m pip install --upgrade pip

#Установка репозитория:

pip install -r requirements.txt

#Ставим для картинок
pip install Pillow

Ставим еще pip install sorl-thumbnail==11.12

#Войти:

cd yatube

#Запуск миграции:

python3 homework.py migrate

#если ошибка то  
python3 homework.py makemigrations

#Создание супер пользователя:

python3 homework.py createsuperuser

#Запуск:

python3 manage.py runserver

АВТО ИСПРАВЛЕНИЕ!!!! https://pypi.org/project/black/ Автоформаттеры Автоформаттеры – это программы, которые автоматически реорганизуют ваш код для соответствия PEP 8. Одна из таких программ — black. Она автоматически форматирует код для приведения его в соответствие с большинством правил PEP 8. Единственное, она ограничивает длину строки до 88 символов, а не до 79, как рекомендовано стандартом. Однако вы можете изменить это, добавив флаг командной строки, как в примере ниже.

Установите black с помощью pip. Для запуска требуется Python 3.6+:

$ pip install black

ЗАПУСК black posts

Если вы хотите изменить ограничение длины строки, можно использовать флаг --line-length:

$ black --line-length=79 posts


# Установка пакета Coverage
pip install coverage

# Перейдите в рабочую директорию проекта (где хранится manage.py) и запустите coverage: выполните 
$ coverage run --source='posts,users' manage.py test -v 2

# покажет отчёт
coverage report

# Все команды отображения работают с созданным отчётом .coverage. После нового запуска 

$ coverage run этот отчёт будет перезаписан.

# Команда coverage html сформирует папку /htmlcov

# не умеет работать с кириллицей. Нужно установить в виртуальное окружение пакет pytils (pip install pytils) 

Выборочный запуск тестов
# Запустит все тесты проекта
python3 manage.py test

# Запустит только тесты в приложении posts
python3 manage.py test posts

# Запустит только тесты из файла test_urls.py в приложении posts
python3 manage.py test posts.tests.test_urls

# Запустит только тесты из класса StaticURLTests для test_urls.py в приложении posts  
python3 manage.py test posts.tests.test_urls.StaticURLTests

# Запустит только тест test_homepage()
# из класса StaticURLTests для test_urls.py в приложении posts 
python3 manage.py test posts.tests.test_urls.StaticURLTests.test_homepage 

python3 manage.py test -v 2
