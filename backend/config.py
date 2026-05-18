import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")


XGBOOST_MODEL_PATH = os.path.join(MODELS_DIR, "xgboost_phishing_model.pkl")
ROBERTA_MODEL_PATH = os.path.join(MODELS_DIR, "RoBERTa_model")


from dotenv import load_dotenv
load_dotenv()
LLAVA_API_URL = os.getenv("LLAVA_API_URL", "")


PHISHING_THRESHOLD = 0.5


WEIGHT_URL = 0.35
WEIGHT_EMAIL = 0.40
WEIGHT_IMAGE = 0.25


WHOIS_YOUNG_DOMAIN_DAYS = 180