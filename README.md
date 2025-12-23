# Анализатор UI логов nginx

Консольное приложение, которое позволяет проанализировать наиболее свежий лог-файли и посчитать набор статистик.

## Оглавление
- [Системные зависимости](#Системные зависимости)
- [Установка](#установка)
- [Использование](#использование)
- [Технологии](#технологии)
-
## Системные зависимости
1. python 3.12 и выше
2. poetry 2.2.1

## Установка

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/timekeeper18/otus_nginx_log_analizer.git
   ```
2. Установка зависимостей: ```python3 -m poetry install --no-root```

## Использование
1. Укажите в конфигурационном файле [log_analyzer.config](log_analyzer.config) параметры запуска:
```python
   {
        "REPORT_SIZE": 200, # количество записей, которое поадет в Отчет (сортировка по максимальному времени исполнения по убыванию)
        "REPORT_DIR": "./report", # директория. в которой будет содержаться итоговый отчет
        "LOG_DIR": "./data", # диреутория, в которой хранятся логи nginx
        "SCRIPT_LOG_FILE": "log_analyzer.log" # лог файл исполнения
   }
```
2. Формать названия файла логов: ```nginx-access-ui.log-<ДАТА>.gz``` (пример: nginx-access-ui.log-20251220.gz)
3. Форма строки логов: ```1.196.116.32 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/banner/25019354 HTTP/1.1" 200 927 "-" "Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5" "-" "1498697422-2190034393-4708-9752759" "dc7161be3" 0.390```
4. Параметры запуска: ```python3 log_analyzer.py --config ./log_analyzer.confi```
5. В результате успешной работы скрипта в директории ```REPORT_DIR``` появится файл с отчетом: ```report-<ДАТА ЛОГ ФАЙЛА>.html``` (пример: report-2025.12.20.html)

## Технологии
Используемые библиотеки
```
black==25.12.0
cfgv==3.5.0
click==8.3.1
coverage==7.13.0
distlib==0.4.0
filelock==3.20.1
flake8==7.3.0
identify==2.6.15
iniconfig==2.3.0
isort==7.0.0
librt==0.7.4
mccabe==0.7.0
mypy==1.19.1
mypy_extensions==1.1.0
nodeenv==1.10.0
packaging==25.0
pathspec==0.12.1
platformdirs==4.5.1
pluggy==1.6.0
pre_commit==4.5.1
pycodestyle==2.14.0
pyflakes==3.4.0
Pygments==2.19.2
pytest==9.0.2
pytest-cov==7.0.0
pytokens==0.3.0
PyYAML==6.0.3
ruff==0.14.9
structlog==25.5.0
typing_extensions==4.15.0
virtualenv==20.35.4```
