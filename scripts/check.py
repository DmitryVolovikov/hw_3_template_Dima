import json
import os
import signal
import subprocess
import sys
import time
import uuid
from pathlib import Path

folder = Path(__file__).resolve().parent.parent
name = 'test_' + uuid.uuid4().hex[:8]
env = dict(os.environ, APP_PORT='0')


def docker(*args):
    return subprocess.check_output(
        ['docker', 'compose', '-p', name, *args],
        cwd=folder, env=env, text=True, timeout=300
    ).strip()


def check(path, method='GET', code=200):
    text = subprocess.check_output(
        ['curl', '-sS', '--max-time', '5', '-X', method,
         '-w', '\n%{http_code}', url + path],
        text=True, timeout=10
    )
    data, status = text.rsplit('\n', 1)
    if int(status) != code:
        raise Exception(path + ': неверный код ' + status)
    return json.loads(data)


def wait():
    for i in range(60):
        try:
            check('/readyz')
            return
        except Exception:
            time.sleep(2)
    raise Exception('приложение не готово')


signal.signal(signal.SIGTERM, lambda *_: sys.exit(1))
step = 'запуск'

try:
    docker('up', '-d', '--build')
    url = 'http://127.0.0.1:' + docker('port', 'app', '8000').splitlines()[0].rsplit(':', 1)[1]
    wait()

    step = 'счётчик'
    if check('/')['count'] != 0:
        raise Exception('не ноль')
    for i in range(1, 4):
        if check('/increment', 'POST')['count'] != i:
            raise Exception('неверный счётчик')
    print('Счётчик OK')

    step = 'пересоздание'
    docker('up', '-d', '--no-deps', '--force-recreate', 'app')
    url = 'http://127.0.0.1:' + docker('port', 'app', '8000').splitlines()[0].rsplit(':', 1)[1]
    wait()
    if check('/')['count'] != 3:
        raise Exception('счётчик сбросился')
    print('Пересоздание OK')

    step = 'Redis'
    app = docker('ps', '-q', 'app')
    docker('stop', 'redis')
    check('/healthz')
    check('/readyz', code=503)
    check('/increment', 'POST', 503)
    docker('start', 'redis')
    wait()
    if docker('ps', '-q', 'app') != app or check('/')['count'] != 3:
        raise Exception('ошибка восстановления')
    if check('/increment', 'POST')['count'] != 4:
        raise Exception('счётчик не увеличился')
    print('Redis OK')

    step = 'копия'
    docker('stop', 'app', 'redis')
    backup = folder / 'backups' / (name + '.tar')
    backup.parent.mkdir(exist_ok=True)
    with open(backup, 'wb') as f:
        subprocess.run(
            ['docker', 'run', '--rm', '-v',
             name + '_redis_data:/data:ro',
             'redis:7.4-alpine', 'tar', '-cf', '-', '-C', '/data', '.'],
            stdout=f, check=True, timeout=300
        )
    print('Копия:', backup)
    print('Все проверки прошли')

except BaseException as e:
    print('Ошибка:', step, e)
    sys.exit(1)

finally:
    try:
        docker('down', '-v')
    except Exception as e:
        print('Ошибка очистки:', e)
        sys.exit(1)