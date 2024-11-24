ip: 51.250.21.100
домен: kras-foodgram2.ddns.net
email: admin@admin.com
пароль: admin

# Проект Foodgram

![workflow status badge](https://github.com/Anastasiia2201/foodgram/actions/workflows/main.yml/badge.svg)

### Описание проекта
Проект «Фудграм» — сайт, на котором пользователи могут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Зарегистрированным пользователям также доступен сервис «Список покупок». Он позволит создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

### Cтек технологий
- Python 3.11.1,
- Django 3.2.3,
- djangorestframework==3.12.4, 
- PostgreSQL 13.10

### Как запустить проект:

1. Создать файл `.env` и заполнить его своими данными. Все необходимые переменные перечислены в файле `.env.example`, находящемся в корневой директории проекта.
2. Скопировать файлы `docker-compose.production.yml` и `.env` в одну директорию на сервер
    ```
    scp -i path_to_SSH/SSH_name docker-compose.production.yml \
    username@server_ip:/home/username/taski/docker-compose.production.yml
    ```
3. Установить Docker Compose на сервер
    ```
    sudo apt update
    sudo apt install curl
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo apt install docker-compose
    ```
4. Запустить Docker Compose в режиме демона
    ```
    sudo docker-compose -f docker-compose.production.yml up -d
    ```
5. Собрать статику и выполнить миграции
    ```
    docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
    docker compose -f docker-compose.production.yml exec backend cp -r /app/collected_static/. /backend_static/static/ 
    docker compose -f docker-compose.production.yml exec backend python manage.py migrate
    ```
6.  Добавить тестовые данные
    ```
    docker compose -f docker-compose.production.yml exec backend python manage.py importcsv
    ```

7. Изменить конфигурацию Nginx:
   ```
   sudo nano /etc/nginx/sites-enabled/default
   ```
   Заменить настройки `location` в секции `server`:

    ```
    location / {
        proxy_set_header Host $http_host;
        proxy_pass http://127.0.0.1:7000;
    }
8. Проверить правильность конфигурации Nginx
    ```
    sudo nginx -t
    ```
9. Перезапустить Nginx
    ```
    sudo service nginx reload
    ```

### Автор
Красько Анастасия
