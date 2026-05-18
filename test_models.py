import sys
sys.path.insert(0, ".")

from backend.services.url_scorer import score_url
from backend.services.email_scorer import score_email

print("=" * 50)
print("URL SCORER TESTS")
print("=" * 50)

urls = [
    "http://secure-login.verify-bank.com/account?user=123",
    "https://www.google.com",
    "http://192.168.1.1/login",
    "https://paypal.com",
]
for url in urls:
    result = score_url(url)
    print(f"URL: {url}")
    print(f"  Score: {result['url_score']} | Label: {result['label']}")
    print()

print("=" * 50)
print("EMAIL SCORER TESTS")
print("=" * 50)

emails = [
    "URGENT: Your account will be suspended! Verify now at http://fakebank.com/login",
    "Hi team, the sprint review is scheduled for Friday at 3pm. Please confirm attendance.",
]
for email in emails:
    result = score_email(email)
    print(f"Email: {email[:60]}...")
    print(f"  Score: {result['email_score']} | Label: {result['label']}")
    print()