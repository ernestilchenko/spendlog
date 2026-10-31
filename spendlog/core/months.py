from datetime import date, datetime, time

from django.utils import timezone


def current_month():
    return timezone.localdate().replace(day=1)


def parse_month(value):
    try:
        return datetime.strptime(value, '%Y-%m').date()
    except (TypeError, ValueError):
        return current_month()


def shift_month(month_start, delta):
    index = month_start.year * 12 + month_start.month - 1 + delta
    return date(index // 12, index % 12 + 1, 1)


def month_bounds(month_start):
    start = timezone.make_aware(datetime.combine(month_start, time.min))
    end = timezone.make_aware(datetime.combine(shift_month(month_start, 1), time.min))
    return start, end
