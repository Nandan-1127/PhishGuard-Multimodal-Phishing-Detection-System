import pickle
import re
import math
import numpy as np
import tldextract
from urllib.parse import urlparse
from backend.config import XGBOOST_MODEL_PATH


print("Loading XGBoost model...")
with open(XGBOOST_MODEL_PATH, "rb") as f:
    _model = pickle.load(f)
print("XGBoost loaded ✅")


FEATURE_COLUMNS = [
    'url_length', 'hostname_length', 'path_length',
    'num_digits', 'num_special_chars', 'num_dots', 'num_hyphens',
    'num_subdomains', 'has_https', 'has_ip', 'has_at',
    'has_suspicious_words', 'url_entropy', 'domain_length', 'tld_length'
]


def _entropy(s: str) -> float:
    if not s:
        return 0.0
    prob = [float(s.count(c)) / len(s) for c in dict.fromkeys(list(s))]
    return -sum(p * math.log2(p) for p in prob)


def _extract_features(url: str) -> dict:
    try:
        url = str(url)
        if not url.startswith("http"):
            url = "http://" + url

        parsed = urlparse(url)
        ext = tldextract.extract(url)

        return {
            'url_length': len(url),
            'hostname_length': len(parsed.netloc),
            'path_length': len(parsed.path),
            'num_digits': sum(c.isdigit() for c in url),
            'num_special_chars': sum(c in "@#$%^&*()-_=+[]{}|;:,.<>?" for c in url),
            'num_dots': url.count('.'),
            'num_hyphens': url.count('-'),
            'num_subdomains': len(ext.subdomain.split('.')) if ext.subdomain else 0,
            'has_https': int(parsed.scheme == 'https'),
            'has_ip': int(bool(re.search(r'\d+\.\d+\.\d+\.\d+', url))),
            'has_at': int('@' in url),
            'has_suspicious_words': int(any(
                w in url.lower() for w in ['login', 'verify', 'bank', 'secure']
            )),
            'url_entropy': _entropy(url),
            'domain_length': len(ext.domain),
            'tld_length': len(ext.suffix)
        }
    except Exception:
        return {k: 0 for k in FEATURE_COLUMNS}


def score_url(url: str) -> dict:
    """
    Returns phishing probability for a URL.
    1.0 = phishing, 0.0 = safe.
    """
    if not url or not url.strip():
        return {"url_score": None, "error": "Empty input"}

    features = _extract_features(url)
    feature_vector = np.array([[features[col] for col in FEATURE_COLUMNS]])

    proba = _model.predict_proba(feature_vector)[0]
    phishing_score = float(proba[1])  

    return {
        "url_score": round(phishing_score, 4),
        "label": "phishing" if phishing_score >= 0.5 else "safe",
        "features_used": features
    }