Foodgram - продуктовый помощник

---

![Workflow Status](https://github.com/leonidz92/foodgram/actions/workflows/main.yml/badge.svg)

---

Описание проекта

Онлайн-сервис Foodgram («Продуктовый помощник») создан для начинающих кулинаров и опытных гурманов. В сервисе пользователи могут:  
- публиковать рецепты,  
- просматривать рецепты других пользователей,  
- добавлять понравившиеся рецепты в список «Избранное»,  
- подписываться на других пользователей,  
- формировать и скачивать список покупок в формате .txt для похода в магазин.  

Проект разворачивается в Docker-контейнерах, включающих:  
- backend-приложение на Django REST Framework,  
- базу данных PostgreSQL,  
- веб-сервер nginx,  
- frontend-контейнер.  

Также реализованы CI/CD процессы:  
- При пуше изменений в главную ветку автоматически запускаются тесты на соответствие требованиям PEP8.  
- После успешных проверок создается Docker-образ backend-контейнера, который загружается в DockerHub и разворачивается на боевом сервере в облаке Yandex.Cloud.  

---

Стек технологий  
- Python  
- Django  
- Django REST Framework  
- PostgreSQL  
- nginx  
- gunicorn  
- docker  
- GitHub Actions  

---

Системные требования  
- Python 3.7+  
- Установленный Docker  
- Платформы: Linux, Windows 

---

Ссылка на проект  

Проект доступен на сервере Yandex Cloud: Foodgram [(https://github.com/yandex-praktikum/foodgram)]

---

Запуск проекта в контейнере  

1. Клонируйте репозиторий и перейдите в папку проекта:  

   
   git clone https://github.com/LeonidZ92/Foodgram.git
   cd Foodgram
   

2. Проверьте доступность портов:  
   - Порт 9090 должен быть свободен для backend.  
   - Порт 5432 должен быть свободен для PostgreSQL.  

3. Создайте файл .env для переменных окружения:  

   
   cd infra
   touch .env
   

   Добавьте в файл .env следующие настройки (параметры по примеру):  

   
   DB_ENGINE=django.db.backends.postgresql
   DB_NAME=postgres
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   DB_HOST=db
   DB_PORT=5432
   SECRET_KEY=************  # Укажите секретный ключ из settings.py
   

   Подсказка: Пример переменных окружения уже находится в файле .env.example.  

4. Установите и запустите контейнеры:  

   
   docker-compose up -d
   

5. Настройте проект:  
   - Выполните миграции:  

     
     docker-compose exec backend python manage.py migrate
     

   - Создайте суперпользователя:  

     
     docker-compose exec backend python manage.py createsuperuser
     

   - Соберите статические файлы:  

     
     docker-compose exec backend python manage.py collectstatic 
     

   - Импортируйте ингредиенты и теги в базу данных:  

     
     docker-compose exec backend python manage.py import_data
     

---

Пример CI/CD  

1. Автоматизация настроена с помощью GitHub Actions.  
2. После пуша в главную ветку запускаются тесты и создается Docker-образ.  
3. Образ автоматически деплоится на сервер Yandex Cloud вместе с:  
   - Nginx-сервером,  
   - PostgreSQL,  
   - Django backend приложением.  

Теперь приложение готово к использованию! 🚀

**Автор**

Проект разработал Зыков Леонид (https://github.com/leonidz92).

