import logging
from typing import Any, Optional, cast

import structlog


def setup_logging(log_file: Optional[str] = None, log_level: str = "INFO") -> Any:
    """
    Настройка логирования с записью в файл и консоль
    """
    # Создаем обработчики
    handlers = []

    # Обработчик для консоли
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    handlers.append(console_handler)

    # Обработчик для файла (если указан)
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(log_level)
        handlers.append(cast(logging.StreamHandler, file_handler))

    # Настраиваем базовый logging
    logging.basicConfig(format="%(message)s", level=log_level, handlers=handlers)

    # Процессоры structlog
    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    structlog_processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ]

    # Форматтеры для разных обработчиков
    console_formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.dev.ConsoleRenderer(),
        foreign_pre_chain=structlog_processors[:-1],  # type: ignore[arg-type]
    )

    json_formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
        foreign_pre_chain=structlog_processors[:-1],  # type: ignore[arg-type]
    )

    # Применяем форматтеры к обработчикам
    console_handler.setFormatter(console_formatter)
    if log_file:
        file_handler.setFormatter(json_formatter)  # type: ignore[has-type]

    # Настраиваем structlog
    structlog.configure(
        processors=structlog_processors,  # type: ignore[arg-type]
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    return structlog.get_logger()
