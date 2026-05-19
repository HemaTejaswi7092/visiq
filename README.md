# ⬡ VISIQ — Intelligent Visual Inspection System

> AI-powered defect detection for PCBs, circuit boards, wafers, and industrial components.

🔗 **Live Demo:** [visiq.vercel.app](https://visiq.vercel.app) *(coming soon)*

---

## ✨ Features

- **AI Defect Analysis** — Groq Vision AI (Llama 4 Scout) detects scratches, cracks, corrosion, solder bridges, burn marks, and more
- **OpenCV Preprocessing Pipeline** — Denoising → Sharpening → CLAHE contrast enhancement before AI analysis
- **Damage Progression Risk Assessment** — Per-defect failure timeline, safety risk, financial impact, and urgency level
- **Live Camera Mode** — Capture directly from webcam for real-time inspection
- **PDF Report Export** — Professional inspection reports with full defect breakdown
- **Inspection History** — SQLite database tracking all past inspections
- **Stats Dashboard** — Total inspections, pass rate, average quality score

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React · CSS-in-JS |
| Backend | FastAPI · Python |
| AI Vision | Groq API (Llama 4 Scout) |
| Image Processing | OpenCV (denoise + sharpen + CLAHE) |
| Database | SQLite |
| PDF Generation | ReportLab |
| Deployment | Vercel (frontend) · Render (backend) |

---

## 🚀 How to Run Locally

### Backend
```bash
cd backend
pip install fastapi uvicorn groq opencv-python-headless reportlab pillow python-multipart
export GROQ_API_KEY=your_groq_api_key_here
uvicorn main:app --reload
```
Backend runs at `http://localhost:8000`
API docs at `http://localhost:8000/docs`

### Frontend
```bash
cd frontend
npm install
npm start
```
Frontend runs at `http://localhost:3000`

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/analyze` | Upload image → get verdict, score, defects |
| POST | `/export-pdf` | Upload image → download PDF report |
| GET | `/history` | Get last 20 inspections |
| GET | `/stats` | Total inspections, pass rate, avg score |
| GET | `/health` | Health check |

---

## 📊 Sample Output

```json
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
```

---

## 👤 Author

**Hema Tejaswi Manchikalapudi**  
MS Computer Science @ UCF | OPT Work Authorized  
📧 mht151103@gmail.com  
🔗 [LinkedIn](https://linkedin.com/in/hematejaswimanchikalapudi) · [GitHub](https://github.com/HemaTejaswi7092)
