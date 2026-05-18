from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from backend.config import ROBERTA_MODEL_PATH
 
print("Loading RoBERTa model...")
_tokenizer = AutoTokenizer.from_pretrained(ROBERTA_MODEL_PATH)
_model = AutoModelForSequenceClassification.from_pretrained(ROBERTA_MODEL_PATH)
_model.eval()
 
_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
_model = _model.to(_device)
print(f"RoBERTa loaded on {_device}")
 
 
def score_email(text: str) -> dict:
    """
    Returns phishing probability for email text.
    LABEL_1 = phishing, LABEL_0 = safe.
 
    BUG FIX: confidence was returning max(probs) which is always the dominant
    class probability. For a safe email (score=0.0, label=safe), max(probs)
    was probs[0]=1.0 which got shown as "Confidence: 100% THREAT" in the UI.
    Fix: return confidence as the probability of the PREDICTED label, and
    also return safe_score so the UI can display both sides correctly.
    """
    if not text or not text.strip():
        return {"email_score": None, "error": "Empty input"}
 
    inputs = _tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=512,
        padding=True
    )
    inputs = {k: v.to(_device) for k, v in inputs.items()}
 
    with torch.no_grad():
        outputs = _model(**inputs)
 
    probs = torch.softmax(outputs.logits, dim=1)
    safe_score = probs[0][0].item()      # LABEL_0 = safe
    phishing_score = probs[0][1].item()  # LABEL_1 = phishing
 
    label = "phishing" if phishing_score >= 0.5 else "safe"
 
   
    confidence = phishing_score if label == "phishing" else safe_score
 
    return {
        "email_score": round(phishing_score, 4),
        "safe_score": round(safe_score, 4),
        "label": label,
        "confidence": round(confidence, 4)
    }