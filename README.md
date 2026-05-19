# PhishGuard: AI-Powered Multimodal Phishing Detection Framework

<p align="center">
  <img src="screenshots/system_architecture.png" alt="PhishGuard Architecture" width="900">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10-blue?style=for-the-badge&logo=python">
  <img src="https://img.shields.io/badge/FastAPI-Backend-green?style=for-the-badge&logo=fastapi">
  <img src="https://img.shields.io/badge/Flask-Frontend-black?style=for-the-badge&logo=flask">
  <img src="https://img.shields.io/badge/XGBoost-URL%20Detection-orange?style=for-the-badge">
  <img src="https://img.shields.io/badge/RoBERTa-Email%20Detection-red?style=for-the-badge">
  <img src="https://img.shields.io/badge/LLaVA-Visual%20Analysis-purple?style=for-the-badge">
</p>

---

## Overview

PhishGuard is an AI-powered multimodal phishing detection framework designed to detect modern phishing attacks using multiple analysis techniques. Unlike traditional phishing detectors that rely on a single modality, PhishGuard combines URL analysis, email classification, screenshot-based visual inspection, WHOIS intelligence, and QR code analysis into one unified cybersecurity system.

The system integrates:

* XGBoost for phishing URL detection
* RoBERTa for phishing email classification
* LLaVA 1.5-7B for screenshot-based phishing analysis
* WHOIS domain intelligence scoring
* QR code phishing detection
* FastAPI backend with Flask frontend
* Multimodal weighted score aggregation

---

# Key Features

* URL phishing detection using XGBoost
* Email phishing detection using RoBERTa
* Screenshot-based webpage analysis using LLaVA
* QR phishing (Quishing) detection
* WHOIS domain intelligence scoring
* Screenshot capture using Playwright
* FastAPI backend API services
* Flask frontend web interface
* Multimodal phishing score aggregation
* Natural-language phishing explanations
* Redirect-chain screenshot capture

---

# System Architecture

<p align="center">
  <img src="screenshots/system_architecture.png" alt="System Architecture" width="1000">
</p>

The architecture contains:

* URL Classification Module (XGBoost)
* Email Classification Module (RoBERTa)
* Screenshot Analysis Module (LLaVA)
* WHOIS Domain Intelligence
* QR Code Analysis
* Multimodal Score Aggregation
* FastAPI Backend Services
* Flask Frontend Interface

---

# Technology Stack

| Component           | Technology   |
| ------------------- | ------------ |
| Backend API         | FastAPI      |
| Frontend            | Flask        |
| URL Detection       | XGBoost      |
| Email Detection     | RoBERTa      |
| Screenshot Analysis | LLaVA 1.5-7B |
| Screenshot Capture  | Playwright   |
| QR Detection        | OpenCV       |
| Domain Intelligence | python-whois |
| Language            | Python       |
| Model Training      | Google Colab |

---

# Project Structure

```bash
PhishGuard/
│
├── backend/
│   ├── services/
│   ├── utils/
│   ├── models/
│   ├── results/
│   ├── notebooks/
│   ├── data/
│   ├── main.py
│   └── config.py
│
├── frontend/
│   ├── static/
│   ├── templates/
│   ├── data/
│   └── app.py
│
├── screenshots/
├── demo/
├── README.md
├── requirements.txt
├── requirements_frontend.txt
└── .gitignore
```

---

# Datasets Used

## URL Dataset

Dataset: `urldata.csv`

* Total URLs: 450,176
* Safe URLs: 77%
* Phishing URLs: 23%

Features extracted:

* URL length
* Hostname length
* Path length
* Number of digits
* Number of dots
* HTTPS presence
* IP address usage
* Suspicious keywords
* URL entropy
* Domain length
* TLD length

---

## Email Dataset

Dataset: `Phishing_Email.csv`

* Total samples: 18,101
* Balanced using random undersampling
* Binary classification

---

# XGBoost URL Detection Module

## Training Configuration

| Parameter                | Value |
| ------------------------ | ----- |
| Trees                    | 400   |
| Max Depth                | 8     |
| Learning Rate            | 0.05  |
| Classification Threshold | 0.7   |
| Train/Test Split         | 80/20 |
| scale_pos_weight         | ~3.35 |

---

## XGBoost Results

| Metric    | Value  |
| --------- | ------ |
| Accuracy  | 99.70% |
| Precision | 1.00   |
| Recall    | 0.99   |
| F1-Score  | 0.99   |

### Confusion Matrix

<p align="center">
  <img src="screenshots/xgboost_confusion_matrix.png" alt="XGBoost Confusion Matrix" width="650">
</p>

---

# RoBERTa Email Detection Module

## Training Details

The RoBERTa model was trained on Google Colab using NVIDIA T4 GPU support because local hardware resources were insufficient for transformer training.

The best model checkpoint was downloaded after training and integrated into the FastAPI backend for inference.

## Hyperparameters

| Parameter         | Value         |
| ----------------- | ------------- |
| Model             | RoBERTa-base  |
| Epochs            | 4             |
| Max Token Length  | 256           |
| Learning Rate     | 2e-5          |
| Optimizer         | AdamW         |
| Weight Decay      | 0.01          |
| Scheduler         | Linear Warmup |
| Gradient Clipping | Enabled       |

---

## RoBERTa Results

| Metric                | Value  |
| --------------------- | ------ |
| Accuracy              | 98.42% |
| Precision             | 98.43% |
| Recall                | 98.42% |
| ROC-AUC               | 0.9987 |
| Misclassified Samples | 33     |

---

## Training Curves

<p align="center">
  <img src="screenshots/roberta_training.png" alt="RoBERTa Training Curves" width="900">
</p>

---

## ROC Curve

<p align="center">
  <img src="screenshots/roberta_roc.png" alt="RoBERTa ROC Curve" width="650">
</p>

---

## Confidence Distribution

<p align="center">
  <img src="screenshots/roberta_confidence_distribution.png" alt="Confidence Distribution" width="750">
</p>

---

# LLaVA Visual Screenshot Analysis

PhishGuard uses LLaVA 1.5-7B for screenshot-based phishing analysis.

The model identifies:

* Fake login pages
* Credential harvesting forms
* Suspicious payment requests
* Urgency messages
* Brand impersonation
* Visual phishing indicators

## Important Implementation Detail

LLaVA was deployed externally through Google Colab and connected to the FastAPI backend using a Cloudflare Tunnel endpoint.

Since the temporary Cloudflare tunnel URL changes after each runtime session, the environment variable containing the endpoint is manually updated before execution.

## LLaVA Performance

| Metric                 | Value    |
| ---------------------- | -------- |
| Screenshot Coverage    | ~85%     |
| Average Inference Time | 8–15 sec |

---

# WHOIS Domain Intelligence

The WHOIS module extracts domain age and assigns phishing risk scores using a multi-tier scoring mechanism.

| Domain Age        | Risk Score |
| ----------------- | ---------- |
| Less than 30 days | 0.95       |
| 31–90 days        | 0.85       |
| 91–180 days       | 0.70       |
| 181–365 days      | 0.55       |
| 1–2 years         | 0.35       |
| 2–5 years         | 0.20       |
| More than 5 years | 0.10       |

---

# QR Phishing Detection

The QR module uses OpenCV to decode uploaded QR images and extract embedded URLs.

The extracted URL is then analyzed using:

* XGBoost phishing detection
* WHOIS domain intelligence

This module helps detect modern Quishing attacks.

---

# Multimodal Score Aggregation

Final phishing verdicts are generated using weighted multimodal aggregation.

| Module              | Weight |
| ------------------- | ------ |
| URL Analysis        | 35%    |
| Email Analysis      | 40%    |
| Screenshot Analysis | 25%    |

Classification thresholds:

| Score Range | Verdict                  |
| ----------- | ------------------------ |
| > 0.75      | High Confidence Phishing |
| 0.50–0.74   | Medium Phishing Risk     |
| 0.30–0.49   | Suspicious               |
| < 0.30      | Safe                     |

---

# Installation & Setup

## Clone Repository

```bash
git clone https://github.com/Nandan-1127/PhishGuard-Multimodal-Phishing-Detection-System.git
cd PhishGuard-Multimodal-Phishing-Detection-System
```

---

## Create Conda Environment

```bash
conda create -n phishing_env python=3.10
conda activate phishing_env
```

---

## Install Backend Dependencies

```bash
pip install -r requirements.txt
```

---

## Install Frontend Dependencies

```bash
pip install -r requirements_frontend.txt
```

---

## Run FastAPI Backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

---

## Run Flask Frontend

```bash
cd frontend
python app.py
```

---

# Model Weights

Due to GitHub file size limitations, large trained model files are hosted externally.

## Download Links

* RoBERTa Model Weights: https://drive.google.com/drive/folders/14FlBVscJicX-30Y0Zu2txXqJ-pXwusWY?usp=drive_link
* RoBERTa Backup Checkpoint: https://drive.google.com/drive/folders/14FlBVscJicX-30Y0Zu2txXqJ-pXwusWY?usp=drive_link

After downloading:

Place files inside:

```bash
backend/models/RoBERTa_model/
backend/backup/
```

---

# Demo Video

Demo video covering:

* URL phishing detection
* Email phishing detection
* QR code analysis
* Screenshot phishing detection
* WHOIS intelligence
* LLaVA explanation system

will be added soon.

---

# Future Improvements

* OCR-based phishing text extraction
* Fine-tuned phishing-specific LLaVA model
* DNS intelligence integration
* Certificate transparency analysis
* Multi-stage webpage snapshot analysis
* Mamba-based email classification

---

# Contributors

* S Nandan
* P Ansika

---

# Acknowledgment

This project was developed as part of cybersecurity and AI research work at:

Indian Institute of Information Technology Design and Manufacturing Jabalpur (IIITDMJ)

---

# License

This project is licensed under the MIT License.
