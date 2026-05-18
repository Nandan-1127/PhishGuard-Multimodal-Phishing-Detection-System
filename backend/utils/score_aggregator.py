from backend.config import PHISHING_THRESHOLD, WEIGHT_URL, WEIGHT_EMAIL, WEIGHT_IMAGE


def aggregate_scores(url_score=None, email_score=None, image_score=None):
    """
    Combines available scores into a final phishing verdict.
    Any score can be None if that analysis wasn't performed.
    All scores are floats between 0.0 and 1.0 (1.0 = phishing).
    """
    scores = []
    weights = []

    if url_score is not None:
        scores.append(url_score)
        weights.append(WEIGHT_URL)

    if email_score is not None:
        scores.append(email_score)
        weights.append(WEIGHT_EMAIL)

    if image_score is not None:
        scores.append(image_score)
        weights.append(WEIGHT_IMAGE)

    if not scores:
        return {
            "final_score": None,
            "verdict": "insufficient_data",
            "confidence": "none"
        }

    
    total_weight = sum(weights)
    normalized = [w / total_weight for w in weights]

    final_score = sum(s * w for s, w in zip(scores, normalized))

    
    if final_score >= 0.75:
        verdict = "phishing"
        confidence = "high"
    elif final_score >= PHISHING_THRESHOLD:
        verdict = "phishing"
        confidence = "medium"
    elif final_score >= 0.30:
        verdict = "suspicious"
        confidence = "low"
    else:
        verdict = "safe"
        confidence = "high"

    return {
        "final_score": round(final_score, 4),
        "verdict": verdict,
        "confidence": confidence,
        "breakdown": {
            "url_score": round(url_score, 4) if url_score is not None else None,
            "email_score": round(email_score, 4) if email_score is not None else None,
            "image_score": round(image_score, 4) if image_score is not None else None,
        }
    }