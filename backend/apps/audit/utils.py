from datetime import date
from .models import DateDim

def get_or_create_date_dim(target_date: date) -> DateDim:
    """
    Get or create a DateDim record for a specific date.
    Required for ActivityLog which uses DateDim as a FK.
    """
    date_id = int(target_date.strftime("%Y%m%d"))
    
    date_dim, created = DateDim.objects.get_or_create(
        id=date_id,
        defaults={
            "full_date": target_date,
            "day": target_date.day,
            "day_name": target_date.strftime("%A"),
            "day_of_week": target_date.weekday() + 1,  # 1-7
            "day_of_year": target_date.timetuple().tm_yday,
            "week_of_year": target_date.isocalendar()[1],
            "iso_week": target_date.isocalendar()[1],
            "month": target_date.month,
            "month_name": target_date.strftime("%B"),
            "quarter": (target_date.month - 1) // 3 + 1,
            "year": target_date.year,
            "is_weekend": target_date.weekday() >= 5,
            "fiscal_month": target_date.month,  # Simplified
            "fiscal_quarter": (target_date.month - 1) // 3 + 1,
            "fiscal_year": target_date.year,
        }
    )
    return date_dim
