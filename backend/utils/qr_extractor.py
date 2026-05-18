import cv2
import numpy as np
import base64
import io
from PIL import Image


def extract_url_from_qr(image_base64: str) -> dict:
    """
    Decodes a QR code image and extracts the URL inside it.
    Uses OpenCV QR detector — no extra DLLs needed on Windows.
    Input: base64 encoded image string.
    """
    try:
        image_data = base64.b64decode(image_base64)
        image = Image.open(io.BytesIO(image_data)).convert("RGB")
        img_array = np.array(image)
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

        detector = cv2.QRCodeDetector()
        data, bbox, _ = detector.detectAndDecode(img_bgr)

        if not data:
            return {"url": None, "error": "No QR code found in image"}

        if data.startswith("http") or data.startswith("www"):
            return {"url": data, "error": None}
        else:
            return {"url": data, "error": "QR content is not a URL"}

    except Exception as e:
        return {"url": None, "error": str(e)}