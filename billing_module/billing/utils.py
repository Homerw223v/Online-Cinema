from enum import Enum
from datetime import datetime
from dateutil.relativedelta import relativedelta
from db.models import DurationUnit


class PaymentState(Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    CANCELED = "canceled"


class DurationAdapter:
    @staticmethod
    def increase_expired(start_dt: datetime, duration: str, duration_unit: DurationUnit):
        if duration_unit == DurationUnit.DAYS:
            return start_dt + relativedelta(days=+duration)
        elif duration_unit == DurationUnit.MONTH:
            return start_dt + relativedelta(month=+duration)
        elif duration_unit == DurationUnit.YEAR:
            return start_dt + relativedelta(years=+duration)
        raise ValueError(f"Error duration unit: {duration_unit}")

    @staticmethod
    def decrease_expired(start_dt: datetime, duration: str, duration_unit: DurationUnit):
        if duration_unit == DurationUnit.DAYS:
            return start_dt + relativedelta(days=-duration)
        elif duration_unit == DurationUnit.MONTH:
            return start_dt + relativedelta(month=-duration)
        elif duration_unit == DurationUnit.YEAR:
            return start_dt + relativedelta(years=-duration)
        raise ValueError(f"Error duration unit: {duration_unit}")
