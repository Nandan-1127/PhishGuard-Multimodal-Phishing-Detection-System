import whois
from datetime import datetime, timezone
from backend.config import WHOIS_YOUNG_DOMAIN_DAYS
import tldextract


def get_domain_info(url: str) -> dict:
    """
    Returns WHOIS info + domain age intelligence.

    FIXES & IMPROVEMENTS:
    1. Handle datetime objects that have no tzinfo properly
    2. Handle list of dates — pick earliest (most accurate registration date)
    3. Add domain age category label for UI display
    4. Better registrar cleaning (some return HTML or long strings)
    5. Add expiry warning if domain expires soon (within 30 days)
    6. whois_score now uses graduated scoring not just binary 0.1/0.8
    """
    try:
        ext = tldextract.extract(url)
        domain = f"{ext.domain}.{ext.suffix}"

        w = whois.whois(domain)

        
        creation_date = w.creation_date
        if isinstance(creation_date, list):
            dates = [d for d in creation_date if d is not None]
            creation_date = min(dates) if dates else None

        
        expiration_date = w.expiration_date
        if isinstance(expiration_date, list):
            dates = [d for d in expiration_date if d is not None]
            expiration_date = max(dates) if dates else None

        now = datetime.now(timezone.utc)

        
        age_days = None
        if creation_date:
            if hasattr(creation_date, 'tzinfo') and creation_date.tzinfo is None:
                creation_date = creation_date.replace(tzinfo=timezone.utc)
            age_days = (now - creation_date).days

        
        expiry_days = None
        expiring_soon = False
        if expiration_date:
            if hasattr(expiration_date, 'tzinfo') and expiration_date.tzinfo is None:
                expiration_date = expiration_date.replace(tzinfo=timezone.utc)
            expiry_days = (expiration_date - now).days
            expiring_soon = 0 < expiry_days < 30

        is_young = age_days is not None and age_days < WHOIS_YOUNG_DOMAIN_DAYS

        
        if age_days is None:
            age_category = "Unknown"
        elif age_days < 30:
            age_category = "Very New (< 1 month) — HIGH RISK"
        elif age_days < 90:
            age_category = "New (< 3 months) — HIGH RISK"
        elif age_days < 180:
            age_category = "Recent (< 6 months) — SUSPICIOUS"
        elif age_days < 365:
            age_category = "Moderate (< 1 year)"
        elif age_days < 365 * 3:
            age_category = "Established (1–3 years)"
        else:
            age_category = "Mature (3+ years) — LOW RISK"

       
        if age_days is None:
            whois_score = 0.5  
        elif age_days < 30:
            whois_score = 0.95
        elif age_days < 90:
            whois_score = 0.85
        elif age_days < 180:
            whois_score = 0.70
        elif age_days < 365:
            whois_score = 0.35
        else:
            whois_score = 0.10

        
        if expiring_soon:
            whois_score = min(1.0, whois_score + 0.15)

        
        registrar = w.registrar
        if registrar and len(str(registrar)) > 60:
            registrar = str(registrar)[:60] + "..."

        return {
            "domain": domain,
            "registrar": registrar,
            "creation_date": str(creation_date) if creation_date else None,
            "expiration_date": str(expiration_date) if expiration_date else None,
            "age_days": age_days,
            "age_category": age_category,
            "is_young_domain": is_young,
            "expiring_soon": expiring_soon,
            "expiry_days": expiry_days,
            "whois_score": round(whois_score, 2),
            "error": None
        }

    except Exception as e:
        return {
            "domain": None,
            "registrar": None,
            "creation_date": None,
            "expiration_date": None,
            "age_days": None,
            "age_category": "Unknown (WHOIS lookup failed)",
            "is_young_domain": None,
            "expiring_soon": False,
            "expiry_days": None,
            "whois_score": 0.5,
            "error": str(e)
        }