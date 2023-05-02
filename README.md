# Дипломный проект студента ЯП Нор Георгия

# ip: 51.250.99.24
# login: test@test.ru
# pass: test

![Deploy badge](https://github.com/Junior-George/foodgram-project-react/actions/workflows/main.yml/badge.svg)

### Описание проекта

'Продуктовый помошник' - простое и удобное в использовании приложение, с помощью которого вы сможете легко найти новые кулинарные рецепты на любой вкус, поделиться своими умениями и знаниями в готовке и следить за творчеством любимых поваров. В приложение встроена функция 'Список покупок', которая быстро лоберет список ингредиентов из тех рецептов, которые вы выбрали!


### Первоначальная подготовка удаленного сервера

Для начала убедитесь, что ВМ вклучена, чтобы подключиться к серверу!

С помощью комманды "ssh username@ip" зайдите на сервер (username - ваш логин, ip - айпи удаленной ВМ )

Обновляем пакеты на удаленном сервере: sudo apt upgrade -y

Устанавливаем необходимое окружение: 

* sudo apt install python3-pip python3-venv git -y
* sudo apt install nginx -y
* sudo ufw enable
* sudo apt install postgresql postgresql-contrib -y
* sudo curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh && sudo rm get-docker.sh
* sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
* sudo chmod +x /usr/local/bin/docker-compose
* sudo systemctl start docker.service && sudo systemctl enable docker.service


### Создание образов front/back-end. Работа в локальном компьютере

|Назначение|Команда|
|--------:|:----------|
| авторизуемся на докерхабе | docker login -u norjunior |
| переходим в папку backend | cd backend |
| строим образ бэкэнда | docker build -t norjunior/backend:v1 . |
| пушим образ | docker push norjunior/backend:v1 |
| возвращаемся в корневую папку | cd - |
| переходим в папку frontend | cd frontend |
| строим образ фронтэнда | docker build -t norjunior/backend:v1 . |
| пушим образ | docker push norjunior/backend:v1 |
| возвращаемся в корневую папку | cd - |
| переходим в папку infra | cd infra |
| копируем файл docker-compose на удаленный сервер | scp docker-compose.yml username@server_ip:/home/username/ |
| копируем файл nging на удаленный сервер | scp nginx.conf username@server_ip:/home/username/ |



### Сборка на локальном компьютере завершена! Теперь возвращаемся на удаленный сервер

* Первым делом собираем контейнеры:

sudo docker-compose up -d --build

* Как только контейнеры соберутся, выполняем миграции:

sudo docker-compose exec backend python manage.py makemigrations recipes

sudo docker-compose exec backend python manage.py migrate --noinput

* Создаем суперпользователя (но это не обязательно)

sudo docker-compose exec backend python manage.py createsuperuser

* Собираем статику:

sudo docker-compose exec backend python manage.py collectstatic --no-input

* На последок заполняем БД ингредиентами и тэгами:

sudo docker-compose exec backend python manage.py add_tags

sudo docker-compose exec backend python manage.py add_ings


* * Ура! Наш сайт готов, и теперь вы можете опробовать его функционал в браузере по сылке:

http://<IP адрес вашего удаленного сервера>/

* * Админка по ссылке:

 http://<IP адрес вашего удаленного сервера>/admin/

### Остановка контейнеров

* Команда для остановки контенеров

docker-compose down -v
