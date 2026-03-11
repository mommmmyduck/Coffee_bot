# bot/utils/time_utils.py
from datetime import datetime
import pytz

def utc_to_msk(utc_dt: datetime) -> datetime:
    """
    Конвертирует UTC время в московское (UTC+3)
    """
    if utc_dt is None:
        return None
    
    # Если время без часового пояса, добавляем UTC
    if utc_dt.tzinfo is None:
        utc_dt = pytz.UTC.localize(utc_dt)
    
    # Конвертируем в Москву
    msk_tz = pytz.timezone('Europe/Moscow')
    return utc_dt.astimezone(msk_tz)

def format_order_time(utc_dt: datetime) -> str:
    """
    Форматирует время заказа в московское время для отображения
    """
    if utc_dt is None:
        return "—"
    
    msk_dt = utc_to_msk(utc_dt)
    return msk_dt.strftime('%H:%M')