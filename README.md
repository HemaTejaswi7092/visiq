# ⬡ VISIQ — Intelligent Visual Inspection System

![React](https://img.shields.io/badge/React-Frontend-61DAFB?logo=react&logoColor=black)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-Llama%204%20Scout-F55036)
![OpenCV](https://img.shields.io/badge/OpenCV-Preprocessing-5C3EE8?logo=opencv&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

AI-powered defect detection for PCBs, circuit boards, wafers, and industrial components — combining an OpenCV preprocessing pipeline with Groq Vision AI to deliver structured inspection reports with risk and severity scoring.

**[🚀 Try the live demo →](https://visiq-frontend.vercel.app)**

<!-- 📸 Add a screenshot or GIF of the dashboard/inspection flow here, e.g.:
![VISIQ Demo](assets/visiq-demo.gif)
-->

---

## Table of Contents
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Run Locally](#-how-to-run-locally)
- [API Endpoints](#-api-endpoints)
- [Sample Output](#-sample-output)

---

## ✨ Features

| | |
|---|---|
| 🔍 **AI Defect Analysis** | Groq Vision AI (Llama 4 Scout) detects scratches, cracks, corrosion, solder bridges, burn marks, and more |
| 🎛️ **OpenCV Preprocessing** | Denoising → sharpening → CLAHE contrast enhancement before AI analysis |
| ⚠️ **Risk Assessment** | Per-defect failure timeline, safety risk, financial impact, and urgency level |
| 📷 **Live Camera Mode** | Capture directly from webcam for real-time inspection |
| 📄 **PDF Report Export** | Professional inspection reports with full defect breakdown |
| 🗄️ **Inspection History** | SQLite database tracking all past inspections |
| 📊 **Stats Dashboard** | Total inspections, pass rate, average quality score |

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React · CSS-in-JS |
| Backend | FastAPI · Python |
| AI Vision | Groq API (Llama 4 Scout) |
| Image Processing | OpenCV (denoise + sharpen + CLAHE) |
| Database | SQLite |
| PDF Generation | ReportLab |
| Deployment | Vercel (frontend) · Railway (backend) |

## 🚀 How to Run Locally

**Backend**
\`\`\`bash
cd backend
pip install fastapi uvicorn groq opencv-python-headless reportlab pillow python-multipart
export GROQ_API_KEY=your_groq_api_key_here
uvicorn main:app --reload
\`\`\`
Runs at `http://localhost:8000` · API docs at `http://localhost:8000/docs`

**Frontend**
\`\`\`bash
cd frontend
npm install
npm start
\`\`\`
Runs at `http://localhost:3000`

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/analyze` | Upload image → get verdict, score, defects |
| POST | `/export-pdf` | Upload image → download PDF report |
| GET | `/history` | Get last 20 inspections |
| GET | `/stats` | Total inspections, pass rate, avg score |
| GET | `/health` | Health check |

## 📊 Sample Output

\`\`\`json
{
  "verdict": "DEFECTIVE",
  "quality_score": 42,
  "summary": "Multiple critical defects detected on PCB surface.",
  "defects": [
    {
      "name": "Solder Bridge",
      "severity": "CRITICAL",
      "location": "Top-left corner, pins 3-4",
      "damage_if_ignored": "Short circuit causing component failure",
      "progression_timeline": "Immediate risk",
      "safety_risk": "HIGH — potential fire hazard",
      "financial_impact": "$500-2000 in component replacement",
      "urgency": "IMMEDIATE_ACTION"
    }
  ]
}
\`\`\`

---

**Built by [Hema Tejaswi Manchikalapudi](https://github.com/HemaTejaswi7092)** · MS CS @ UCF
📧 mht151103@gmail.com · [LinkedIn](https://www.linkedin.com/in/hematejaswimanchikalapudi)
