# Установка self-hosted
1) git clone https://github.com/getsentry/self-hosted.git
2) запустить ./install.sh
    в запросах скрипта можно 
    - отключить сбор мертик в помощь разработчику
    - создать пользователя

# запуск
docker compose up -d

# Проблемы с CSRF
добавить в файл ./sentry/config.yml
system.url-prefix: http://<ip/dns>:9000

https://github.com/getsentry/self-hosted/issues/2751
