import ipaddress
from models.ip_location import IPLocation


def resolve_ip_location(db, ip: str) -> str:
    """
    Возвращает человеко-читаемую локацию для IP.
    Если локация не найдена — возвращает сам IP.
    """
    try:
        ip_int = int(ipaddress.ip_address(ip))
    except ValueError:
        # если вдруг в Device лежит не IP — возвращаем как есть
        return ip

    locations = db.query(IPLocation).all()

    for loc in locations:
        try:
            start = int(ipaddress.ip_address(loc.ip_start))
            end = int(ipaddress.ip_address(loc.ip_end))
        except ValueError:
            continue

        if start <= ip_int <= end:
            return loc.label

    return ip
