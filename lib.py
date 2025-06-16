from enum import StrEnum

class AlertLevel(StrEnum):
    NOTIFY = 'notify'
    FILTER = 'filter'
    ERROR = 'error'