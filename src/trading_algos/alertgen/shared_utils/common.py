import logging
import random


LOGGER = logging.getLogger(__name__)


class TREND:
    UNKNOWN = "NOTKNOWN"
    DOWN = "DOWN"
    RANGE_DOWN = "RANGE_DOWN"
    RANGE_UP = "RANGE_UP"
    UP = "UP"

    LIST = [UNKNOWN, DOWN, RANGE_DOWN, RANGE_UP, UP]

    @staticmethod
    def to_int(trend_str):
        try:
            return TREND.LIST.index(trend_str)
        except Exception:
            LOGGER.error("TREND to_int for %s", trend_str)
            return -1

    @staticmethod
    def from_int(int_in):
        try:
            return TREND.LIST[int_in]
        except Exception:
            LOGGER.error("TREND from_int for int=%s", int_in)
            return TREND.UNKNOWN

    @staticmethod
    def random_trend():
        return TREND.from_int(random.randint(1, 4))

    @staticmethod
    def average(list_in, weights):
        list_in_int = []
        for item in list_in:
            list_in_int.append(TREND.to_int(item))

        total = 0.0
        total_weight = 0.0
        for item_int, weight in zip(list_in_int, weights):
            total += float(item_int) * float(weight)
            total_weight += float(weight)
        try:
            average_raw = total / total_weight
        except Exception:
            average_raw = 0

        return TREND.from_int(round(average_raw))


class CANDLE_COLOUR:
    GREEN = "green"
    WHITE = "white"
    RED = "red"
