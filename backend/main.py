from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import base64

from backend.services.url_scorer import score_url
from backend.services.email_scorer import score_email
from backend.services.screenshot_scorer import score_screenshot
from backend.services.screenshot_capture import capture_screenshot_sync
from backend.services.whois_service import get_domain_info
from backend.utils.score_aggregator import aggregate_scores
from backend.utils.qr_extractor import extract_url_from_qr

app = FastAPI(
    title="Multimodal Phishing Detector",
    description="Detects phishing using XGBoost (URL), RoBERTa (Email), LLaVA (Screenshot)",
    version="1.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class URLRequest(BaseModel):
    url: str

class EmailRequest(BaseModel):
    text: str

class FullScanRequest(BaseModel):
    url: Optional[str] = None
    email_text: Optional[str] = None
    capture_screenshot: Optional[bool] = False


@app.get("/")
def root():
    return {"status": "running", "version": "1.1.0"}

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/scan/url")
def scan_url(request: URLRequest):
    """Score URL using XGBoost + WHOIS domain age intelligence."""
    url_result = score_url(request.url)
    whois_result = get_domain_info(request.url)

    url_score = url_result.get("url_score")


    if url_score is not None and whois_result.get("whois_score") is not None:
        w_score = whois_result["whois_score"]
        if whois_result.get("is_young_domain"):
            
            boost = (w_score - 0.1) * 0.3   
            url_score = min(1.0, url_score + boost)

    return {
        "url": request.url,
        "url_score": round(url_score, 4) if url_score is not None else None,
        "label": "phishing" if (url_score or 0) >= 0.5 else "safe",
        "features_used": url_result.get("features_used"),
        "whois": whois_result
    }


@app.post("/scan/email")
def scan_email(request: EmailRequest):
    """Score email using RoBERTa. Returns phishing score + correct confidence."""
    result = score_email(request.text)
    return {
        "email_score": result.get("email_score"),
        "safe_score": result.get("safe_score"),
        "label": result.get("label"),
        "confidence": result.get("confidence")
    }


@app.post("/scan/screenshot")
def scan_screenshot_url(request: URLRequest):
    """
    Capture screenshot + analyze with LLaVA.
    Returns main screenshot + redirect chain screenshots.
    """
    capture = capture_screenshot_sync(request.url)
    image_result = {"image_score": None, "llava_response": None, "error": "LLaVA not configured"}

    if capture.get("screenshot_base64"):
        image_result = score_screenshot(
            capture["screenshot_base64"],
            url=request.url
        )

    return {
        "url": request.url,
        "final_url": capture.get("final_url"),
        "has_redirect": capture.get("has_redirect"),
        "redirect_chain": capture.get("redirect_chain", []),
        "redirect_chain_detail": capture.get("redirect_chain_detail", []),
        "redirect_screenshots": capture.get("redirect_screenshots", []),
        "screenshot_base64": capture.get("screenshot_base64"),
        "image_score": image_result.get("image_score"),
        "llava_response": image_result.get("llava_response"),
        "capture_error": capture.get("error")
    }


@app.post("/scan/full")
def full_scan(request: FullScanRequest):
    url_score = None
    email_score = None
    image_score = None
    whois_result = None
    screenshot_data = None

    if request.url:
        url_result = score_url(request.url)
        url_score = url_result.get("url_score")
        whois_result = get_domain_info(request.url)
        if url_score is not None and whois_result.get("is_young_domain"):
            w_score = whois_result.get("whois_score", 0.5)
            boost = (w_score - 0.1) * 0.3
            url_score = min(1.0, url_score + boost)

    if request.email_text:
        email_result = score_email(request.email_text)
        email_score = email_result.get("email_score")

    if request.url and request.capture_screenshot:
        capture = capture_screenshot_sync(request.url)
        screenshot_data = {
            "final_url": capture.get("final_url"),
            "has_redirect": capture.get("has_redirect"),
            "redirect_chain": capture.get("redirect_chain", []),
            "redirect_screenshots": capture.get("redirect_screenshots", []),
            "screenshot_base64": capture.get("screenshot_base64"),
        }
        if capture.get("screenshot_base64"):
            image_result = score_screenshot(capture["screenshot_base64"], url=request.url)
            image_score = image_result.get("image_score")

    verdict = aggregate_scores(url_score=url_score, email_score=email_score, image_score=image_score)

    return {
        "verdict": verdict,
        "whois": whois_result,
        "screenshot": screenshot_data
    }


@app.post("/scan/qr")
async def scan_qr(file: UploadFile = File(...)):
    contents = await file.read()
    image_b64 = base64.b64encode(contents).decode("utf-8")
    qr_result = extract_url_from_qr(image_b64)

    if qr_result.get("error") or not qr_result.get("url"):
        return {"qr_url": None, "error": qr_result.get("error", "No QR URL found")}

    extracted_url = qr_result["url"]
    url_result = score_url(extracted_url)
    whois_result = get_domain_info(extracted_url)

    url_score = url_result.get("url_score")
    if url_score is not None and whois_result.get("is_young_domain"):
        w_score = whois_result.get("whois_score", 0.5)
        boost = (w_score - 0.1) * 0.3
        url_score = min(1.0, url_score + boost)

    verdict = aggregate_scores(url_score=url_score)

    return {
        "qr_url": extracted_url,
        "url_score": round(url_score, 4) if url_score is not None else None,
        "label": "phishing" if (url_score or 0) >= 0.5 else "safe",
        "features_used": url_result.get("features_used"),
        "whois": whois_result,
        "verdict": verdict
    }