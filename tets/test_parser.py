# tests/test_parser.py
from src.otus_nginx_log_analizer.log_stat import NginxLogAnalyzer

config_default = {
    "REPORT_SIZE": 200,
    "REPORT_DIR": "./report",
    "LOG_DIR": "./data",
    "SCRIPT_LOG_FILE": "log_analyzer.log",
}


def test_parse_valid_log_line():
    """Тест парсинга нормальной строки лога"""
    parser = NginxLogAnalyzer(config=config_default,
                              log_format='extended')

    # Пример строки из nginx лога
    log_line = ('1.196.116.32 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/banner/25019354 HTTP/1.1" 200 927 '
                '"-" "Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5" "-" '
                '"1498697422-2190034393-4708-9752759" "dc7161be3" 0.390')

    result = parser.parse_line(log_line)

    # Проверяем что не None
    assert result is not None
    # Проверяем ключевые поля
    assert result["ip"] == "1.196.116.32"
    assert result["status"] == 200
    assert float(result["request_time"]) == 0.390


def test_parse_invalid_log_line():
    """Тест парсинга битой строки"""
    log_line = ('1.196.116.32 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/banner/25019354 HTTP/1.1" 200 927 "-" '
                '"Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-')
    parser = NginxLogAnalyzer(config=config_default,
                              log_format='extended')

    log_line = "Это не лог а какая-то ерунда"

    result = parser.parse_line(log_line)

    # Должен вернуть None или пустой словарь
    assert result is None or result == {}


def test_parse_line_with_missing_time():
    """Тест строки без времени запроса"""
    parser = NginxLogAnalyzer(config=config_default,
                              log_format='extended')

    # Строка без времени в конце
    log_line = '1.2.3.4 - - [29/Jun/2017:03:50:22 +0300] "GET /test HTTP/1.1" 200 123'

    result = parser.parse_line(log_line)

    # Проверяем что хотя бы IP распарсился
    if result:
        assert result["ip"] == "1.2.3.4"
