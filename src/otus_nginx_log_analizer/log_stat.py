import gzip
import json
import os
import re
from datetime import datetime, date
from os import DirEntry
from pathlib import Path
from string import Template
from typing import List, Dict, Optional, Generator, Any

from src.otus_nginx_log_analizer.logger import setup_logging
from src.otus_nginx_log_analizer.models import Stat

# log = logger.bind(file_name=os.path.basename(__file__))
log = setup_logging()


class NginxLogAnalyzer:
    """
    Класс для анализа логов nginx.
    Поддерживает несколько форматов включая расширенный с дополнительными полями.
    """

    # Регулярные выражения для парсинга логов
    LOG_FORMATS = {
        'extended': r'(?P<ip>\S+) (?P<client_id>\S+) (?P<user>\S+) \[(?P<time>[^\]]+)\] "(?P<method>\S+) '
                    r'(?P<path>\S+) (?P<protocol>\S+)" (?P<status>\d+) (?P<size>\S+) "(?P<referrer>[^"]*)" '
                    r'"(?P<agent>[^"]*)" "(?P<forwarded_for>[^"]*)" "(?P<request_id>[^"]*)" '
                    r'"(?P<upstream_cache_status>[^"]*)" (?P<request_time>\S+)'
    }

    DATE_FORMAT = {
        'base': '%Y%m%d',
    }

    UI_NAME_PATTERN = r'nginx-access-ui\.log-\d{8}\.gz$'

    def __init__(self, config: dict, log_format: str | None = 'extended'):
        """
        Инициализация анализатора логов.

        :log_path: Путь до директории с логами
        :log_format: Формат лога ('extended'...)
        """
        self.template_dir: Path
        self.__report_dir: Path
        self.__log_dir: Path
        self.log_date: date

        if log_format not in self.LOG_FORMATS:
            raise ValueError(f"Поддерживаемые форматы: {list(self.LOG_FORMATS.keys())}")
        base_path = Path(__file__).parent.parent.parent  # выходим на уровень проекта

        # Обрабатываем входной путь

        if config.get('REPORT_DIR', '').startswith('./'):
            self.template_dir = base_path / str(config.get('REPORT_DIR'))[2:]
            self.__report_dir = base_path / str(config.get('REPORT_DIR'))[2:]
        else:
            self.template_dir = Path(str(config.get('REPORT_DIR')))
            self.__report_dir = Path(str(config.get('REPORT_DIR')))
        if config.get('LOG_DIR', '').startswith('./'):
            self.__log_dir = base_path / str(config.get('LOG_DIR'))[2:]
        else:
            self.__log_dir = Path(str(config.get('LOG_DIR')))

        self.log_format = log_format

        self.pattern = re.compile(self.LOG_FORMATS[log_format])
        self.pattern_ui_log = re.compile(self.UI_NAME_PATTERN)
        self.entries = list[Any]
        self.__report_size = config.get('REPORT_SIZE')

    @staticmethod
    def __is_valid_gzip(filepath: DirEntry) -> bool:
        """
        Проверяет, можно ли открыть файл как GZIP.

        :filepath: путь до файла
        :return: Истина, в случае если это архив и Ложь - в противном случае
        """
        try:
            with gzip.open(filepath, 'rb') as f:
                # Пробуем прочитать немного данных
                f.read(1)
                return True
        except (gzip.BadGzipFile, OSError, FileNotFoundError):
            return False

    @staticmethod
    def __format_float(value: float = 0.0) -> float:
        return round(float(value), 2) if value else 0.00

    def __get_file_date(self, f_name: DirEntry) -> datetime | None:
        """
        Извлекает дату из имени файла.

        :param f_name: Полный путь до файла
        :return: Дата файла
        """
        f_date = None
        try:
            n_ = os.path.basename(f_name)
            _ = os.path.splitext(f_name.name)
            _name, f_extension = os.path.splitext(f_name.name) \
                if self.__is_valid_gzip(filepath=f_name) else [n_, None]
            f_date = _name.split('-')[-1]
            f_date = datetime.strptime(f_date, self.DATE_FORMAT['base'])
        except Exception as exc:
            log.error(exc)
            f_date = None
        return f_date

    def report_render(self, report_template: str = 'report.html',
                      table_json: list[dict] | None = None) -> str | None:
        """
        Создание файла с отчетом.

        :param report_template: Наименование файла шаблона отчет
        :param table_json: Посчитанная статистика по логам
        :return: Успех / не успех
        """
        full_path = os.path.join(self.template_dir, report_template)

        # Проверяем существование файла
        assert os.path.isfile(full_path), f"Файл не найден: {full_path}"
        assert table_json, f"{self.__log_dir} Статистика не посчитана"
        try:
            with open(os.path.join(self.template_dir, report_template), mode='r', encoding='utf-8') as f:
                template_str = f.read()

            # Создаем шаблок из прочитанной строки (файла)
            template = Template(template_str)
            # заменяем через json.dumps, чтобы исключить запрещенные символы для js
            js_code = template.safe_substitute(table_json=json.dumps(table_json))
            report_file = os.path.join(self.__report_dir, f'report-{datetime.strftime(self.log_date,
                                                                                      '%Y.%m.%d')}.html')
            report_name = os.path.join(self.template_dir, report_file)
            with open(report_name, mode='w', encoding='utf-8') as f:
                f.write(js_code)
        except Exception as exc:
            log.error(exc)
            return None
        return report_name

    def get_most_recent_log(self) -> str | None:
        """
        Получаем Путь к файлу с наиболее свежей датой.

        :return: Путь к файлу с наиболее сежей датой
        """
        file_names: List = []
        f_name: str | None = None
        assert os.path.isdir(self.__log_dir), f"{self.__log_dir} не является директорией"
        for file_name in os.scandir(self.__log_dir):
            match = self.pattern_ui_log.match(file_name.name)
            if match:
                if file_name.is_file():
                    f_date = self.__get_file_date(file_name)
                    file_names.append([file_name.name, f_date])
        if file_names:
            f_name, self.log_date = sorted(file_names, key=lambda x: x[1])[-1]
        return f_name

    def parse_line(self, line: str) -> Optional[Dict]:
        """
        Парсинг одной строки лога.

        :line: Строка лога
        :return: Словарь с полями или None при ошибке
        """
        line = line.strip()
        if not line:  # Пропускаем пустые строки
            return None

        # Удаляем начальные и конечные пробелы, заменяем двойные пробелы
        line = re.sub(r'\s+', ' ', line)

        # Пробуем парсить в зависимости от формата
        match = self.pattern.match(line)
        if not match:
            return None
        entry = match.groupdict()

        # Преобразование типов
        try:
            entry['status'] = int(entry['status'])
            entry['size'] = int(entry['size']) if entry['size'] != '-' else 0

            # Для extended формата парсим время запроса
            if 'request_time' in entry:
                try:
                    entry['request_time'] = float(entry['request_time'])
                except (ValueError, TypeError):
                    entry['request_time'] = 0.0

            # Парсинг времени
            time_str = entry['time'].split()[0]  # Берем только дату без смещения часового пояса
            try:
                entry['time'] = datetime.strptime(time_str, '%d/%b/%Y:%H:%M:%S')
            except ValueError:
                # Пробуем альтернативные форматы
                try:
                    entry['time'] = datetime.strptime(time_str, '%Y-%m-%d:%H:%M:%S')
                except ValueError:
                    log.error(f"Неизвестный формат времени: {time_str}")
                    return None

        except (ValueError, KeyError) as e:
            log.error(f"Ошибка парсинга строки: {line[:100]}...")
            log.error(f"Ошибка: {e}")
            return None

        return entry

    def read_logs(self, file_: str, encoding: str = 'utf-8') -> Generator[dict, None, None]:
        """
        Чтение логов из файла с использованием генератора.

        :file_: Имя файла логов
        :encoding: Кодировка, с которой необходимо читать файл логов

        Yields: dict: Распарсенная запись лога
        """
        filepath = os.path.join(self.__log_dir, file_)
        # Проверяем, является ли файл gzip
        is_gzip = filepath.endswith('.gz')
        open_func = gzip.open if is_gzip else open
        mode = 'rt' if is_gzip else 'r'

        log.info(f"Чтение файла: {filepath} (формат: {self.log_format})")

        try:
            with open_func(filepath, mode, encoding=encoding) as f:
                lines_read = 0
                successful = 0

                for line_num, line in enumerate(f, 1):
                    lines_read += 1
                    entry = self.parse_line(line) if line else None
                    if entry:
                        successful += 1
                        yield entry

                    # Выводим прогресс каждые 10000 строк
                    if lines_read % 10000 == 0:
                        log.info(f"  Обработано {lines_read} строк, успешно: {successful}")

                log.info(f"Всего строк: {lines_read}, успешно распаршено: {successful}")

        except UnicodeDecodeError:
            log.warning("Ошибка выбора кодировки файла при чтении")
            # Пробуем другую кодировку
            if encoding != 'latin-1':
                # Для рекурсивного вызова тоже нужно вернуть генератор
                yield from self.read_logs(file_=file_, encoding='latin-1')
        except Exception as e:
            log.error(f"Ошибка при чтении файла {filepath}: {e}")

    @staticmethod
    def get_median(row: list) -> float:
        """
        Поиск медианного значени в массиве.

        :param row: Список значений, по которым надо найти медиану
        :return: Медианное значение
        """
        median: float
        sorted_row = sorted(row)
        n = len(sorted_row)

        if n % 2 == 1:
            # Нечетное количество элементов
            median = sorted_row[n // 2]
        else:
            # Четное количество элементов
            median = (sorted_row[n // 2 - 1] + sorted_row[n // 2]) / 2
        return median

    def get_statistics(self, file_: str | None) -> List[Dict]:
        """
        Подсчета основных статистик по данных лога
        count - сколько раз встречается URL, абсолютное значение
        count_perc - сколько раз встречается URL, в процентнах относительно общего числа запросов
        time_sum - суммарный $request_time для данного URL’а, абсолютное значение
        time_perc - суммарный $request_time для данного URL’а, в процентах относительно общего $request_time всех запросов
        time_avg - средний $request_time для данного URL’а
        time_max - максимальный $request_time для данного URL’а
        time_med - медиана $request_time для данного URL’а

        :return: List[Dict] Посчитанную статистику
        """
        lines = 0
        total_request_time = 0
        url_stat: dict = {}
        med: dict = {}
        if file_ is None:
            return []
        for line in self.read_logs(file_=file_):
            lines += 1
            total_request_time += line.get('request_time', 0)
            if u_data := url_stat.get(line.get('path')):
                # Запоминаем данные для подсчета медианы
                if med[line.get('path')] is None:
                    med[line.get('path')] = [line.get('path')]
                else:
                    med[line.get('path')].append(line.get('request_time'))
                u_data = Stat(**u_data)

                url_stat[line.get('path')] = Stat(url=line.get('path', ''),
                                                  count=u_data.count + 1,
                                                  count_perc=100 * (u_data.count + 1) / lines,
                                                  time_sum=u_data.time_sum + line.get('request_time', 0.0),
                                                  time_perc=100 * (u_data.time_sum + line.get(
                                                      'request_time', 0.0)) / total_request_time,
                                                  time_avg=u_data.time_sum / (u_data.count + 1),
                                                  time_max=line.get('request_time', 0.0)
                                                  if line.get(
                                                      'request_time', 0.0) > u_data.time_max else u_data.time_max,
                                                  time_med=self.get_median(med[line.get('path', '')])).__dict__
            else:
                if line.get('path'):
                    # Запоминаем данные для подсчета медианы
                    med[line.get('path', '')] = [line.get('request_time', 0.0)]
                    url_stat[line.get('path', '')] = Stat(url=line.get('path', ''),
                                                          count=1,
                                                          count_perc=100 / lines,
                                                          time_sum=line.get('request_time', 0.0),
                                                          time_perc=100 * line.get('request_time',
                                                                                   0) / total_request_time,
                                                          time_avg=line.get('request_time', 0.0),
                                                          time_max=line.get('request_time', 0.0),
                                                          time_med=line.get('request_time', 0.0)
                                                          ).__dict__
        return sorted(list(url_stat.values()), key=lambda x: x['time_sum'], reverse=True)[:self.__report_size]


# Тестирование с вашим форматом логов
if __name__ == "__main__":
    config = {
        "REPORT_SIZE": 200,
        "REPORT_DIR": "/home/akhmadiev/PycharmProjects/otus_nginx_log_analizer/report",
        "LOG_DIR": "/home/akhmadiev/PycharmProjects/otus_nginx_log_analizer/data"
    }
    log.info("=== Тестирование парсера для расширенного формата nginx ===")

    # Создаем анализатор для extended формата
    analyzer = NginxLogAnalyzer(config=config,
                                log_format='extended')
    file_ = analyzer.get_most_recent_log()
    v = analyzer.get_statistics(file_=file_)
    log.info(v[:])
    analyzer.report_render(table_json=v)
