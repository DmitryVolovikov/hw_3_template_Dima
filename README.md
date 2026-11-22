# ДЗ 3. Docker

## Запуск

Сначала нужно скопировать `.env.example` в `.env`

`Copy-Item .env.example .env`

Запускаем контейнеры

`docker compose up -d --build`

Приложение работает на http://localhost:8080

Проверить можно так

`curl.exe http://localhost:8080/`

`curl.exe -X POST http://localhost:8080/increment`

## Настройки

В `.env` можно менять порт и приветствие

- `APP_PORT` - порт приложения
- `GREETING` - приветствие

## SQLite

`docker compose down`

`docker compose -f compose.sqlite.yaml up -d --build`

Данные хранятся в volume `counter_data` и не пропадают после удаления контейнера

## Redis

`docker compose -f compose.sqlite.yaml down`

`docker compose up -d --build`

Здесь уже используется Redis. Данные сохраняются в `redis_data`

## Проверка

`python scripts/check.py`

Скрипт проверяет счётчик и сохранение данных после пересоздания контейнера. Потом отключает Redis и проверяет восстановление. В конце создаёт резервную копию и удаляет тестовые контейнеры

Логи проверок лежат в `reports/`

Резервные копии в `backups/`