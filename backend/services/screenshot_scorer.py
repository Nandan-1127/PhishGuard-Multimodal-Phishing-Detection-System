import httpx
from backend.config import LLAVA_API_URL


def score_screenshot(screenshot_base64: str, url: str = "") -> dict:
    """
    Sends screenshot to LLaVA service running on Colab via tunnel.
    Returns image-based phishing score.
    """
    if not LLAVA_API_URL:
        return {
            "image_score": None,
            "llava_response": None,
            "error": "LLAVA_API_URL not configured"
        }

    if not screenshot_base64:
        return {
            "image_score": None,
            "llava_response": None,
            "error": "No screenshot provided"
        }

    try:
        payload = {
            "screenshot_base64": screenshot_base64,
            "url": url
        }
        response = httpx.post(
            f"{LLAVA_API_URL}/analyze",
            json=payload,
            timeout=60.0
        )
        response.raise_for_status()
        data = response.json()

        return {
            "image_score": data.get("image_score"),
            "llava_response": data.get("llava_response"),
            "error": None
        }

    except Exception as e:
        return {
            "image_score": None,
            "llava_response": None,
            "error": str(e)
        }