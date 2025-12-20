import argparse
import json
import os

from src.otus_nginx_log_analizer.log_stat import NginxLogAnalyzer
from src.otus_nginx_log_analizer.logger import setup_logging

# Путь до конфигурайионного файла по умолчанию
DEFAULT_CONF_FILE = './log_analyzer.config'


def main():
    config_default = {
        "REPORT_SIZE": 200,
        "REPORT_DIR": "./report",
        "LOG_DIR": "./data",
        "SCRIPT_LOG_FILE": "log_analyzer.log",
    }
    parser = argparse.ArgumentParser(description='Скрипт анализа логов UI Nginx')
    parser.add_argument('-c', '--config',
                        type=str,
                        required=False,
                        help=f'Путь к конфигурационному файлу, если не указан, то по умолчанию: {DEFAULT_CONF_FILE}')

    args = parser.parse_args()
    log = setup_logging()
    log.info("=== Тестирование парсера для расширенного формата nginx ===")
    cf = args.config
    # Проверяем существование файла
    if not cf or not os.path.isfile(cf):
        log.info(f"Конфигурационный файл не передан, использую значения по умолчанию: {DEFAULT_CONF_FILE}")
        cf = DEFAULT_CONF_FILE
        assert os.path.isfile(cf), "Конфигурационный файл не найден!"

        with (open(cf, 'r', encoding='utf-8') as f):
            lines = f.read()
        config = json.loads(lines) if lines else {}
        config_default.update(config)
    else:
        # Используем конфиг
        log.info(f"Используем конфиг: {cf}")
        assert os.path.isfile(cf), "Конфигурационный файл не найден!"
        with open(cf, 'r', encoding='utf-8') as f:
            lines = f.read()
        config = json.loads(lines) if lines else {}
        # Создаем анализатор для extended формата     "REPORT_DIR": "./report",
        config_default.update(config)
        log.info(f"Конфигурация обновлена: {config_default}")
    try:
        analyzer = NginxLogAnalyzer(config=config_default,
                                    log_format='extended')
        file_ = analyzer.get_most_recent_log()
        v = analyzer.get_statistics(file_=file_)
        if v:
            if report_name := analyzer.report_render(table_json=v):
                log.info(f"=== Анализ логов nginx UI завершен: '{report_name}' ===")
            else:
                log.error(f"=== Формирование файла отчета завершилось с ошибкой ===")
        else:
            log.info("=== Директория с логами nginx не содержит логов UI===")
    except KeyboardInterrupt as e:
        log.info('=== Формирование файла отчета завершилось с ошибкой: прервано пользователем ===')
    except Exception as e:
        log.error('=== Формирование файла отчета завершилось с ошибкой ===', e)


if __name__ == "__main__":
    # python log_analyzer.py --config log_analyzer.config
    main()
