from dataclasses import dataclass


@dataclass
class Stat:
    url: str
    count: int = 0
    count_perc: float = 0
    time_avg: float = 0
    time_sum: float = 0
    time_perc: float = 0
    time_max: float = 0
    time_med: float = 0

    def __post_init__(self) -> None:
        """Автоматически вызывается после инициализации"""
        self.round_floats()

    def round_floats(self, precision: int = 2) -> "Stat":
        """
        Округляет все float-поля до заданной точности
        precision: количество знаков после запятой (по умолчанию 3)
        """
        # Округляем каждое float-поле
        self.count_perc = round(self.count_perc, precision)
        self.time_avg = round(self.time_avg, precision)
        self.time_sum = round(self.time_sum, precision)
        self.time_perc = round(self.time_perc, precision)
        self.time_max = round(self.time_max, precision)
        self.time_med = round(self.time_med, precision)

        # Проверяем границы для процентов (0-100)
        self.count_perc = max(0, min(100, int(self.count_perc)))
        self.time_perc = max(0, min(100, int(self.time_perc)))

        return self  # для цепочки вызовов
