from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import numpy as np
import cv2
import base64
import json
import re
import time
import sqlite3
import io
import datetime
from groq import Groq
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch

app = FastAPI(title="VISIQ API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Groq()  # uses GROQ_API_KEY env var

# ── DATABASE ──
def init_db():
    conn = sqlite3.connect("visiq_history.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS inspections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            filename TEXT,
            verdict TEXT,
            quality_score INTEGER,
            defect_count INTEGER,
            material_type TEXT,
            summary TEXT,
            processing_time_ms REAL
        )
    """)
    conn.commit()
    conn.close()

init_db()

def save_inspection(filename, result, processing_time):
    conn = sqlite3.connect("visiq_history.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO inspections
        (timestamp, filename, verdict, quality_score, defect_count,
         material_type, summary, processing_time_ms)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.datetime.now().isoformat(),
        filename,
        result.get("verdict"),
        result.get("quality_score"),
        len(result.get("defects", [])),
        result.get("material_type"),
        result.get("summary"),
        processing_time
    ))
    conn.commit()
    conn.close()

# ── IMAGE PREPROCESSING ──
def preprocess_image(image_array):
    denoised = cv2.fastNlMeansDenoisingColored(image_array, None, 10, 10, 7, 21)
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharpened = cv2.filter2D(denoised, -1, kernel)
    lab = cv2.cvtColor(sharpened, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    enhanced = cv2.merge([l, a, b])
    enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
    return enhanced

# ── PROMPT ──
SYSTEM_PROMPT = """You are an expert industrial quality control engineer with 20+ years of experience inspecting circuit boards, PCBs, semiconductors, wafers, and manufactured products.

Analyze the image and respond ONLY with a valid JSON object. No markdown, no backticks, no text outside JSON.

Use exactly this structure:
{
  "verdict": "APPROVED" | "DEFECTIVE" | "REVIEW",
  "confidence": <integer 0-100>,
  "quality_score": <integer 0-100>,
  "material_type": "<what this item is>",
  "summary": "<one sentence expert summary>",
  "overall_risk": "HIGH" | "MEDIUM" | "LOW",
  "estimated_remaining_life": "<estimated lifespan if defects not addressed>",
  "defects": [
    {
      "label": "<defect name>",
      "severity": "critical" | "major" | "minor",
      "description": "<technical description>",
      "location": "<where on image>",
      "damage_if_ignored": "<what damage occurs if not fixed>",
      "progression_timeline": "<realistic timeline from now to failure>",
      "safety_risk": "HIGH" | "MEDIUM" | "LOW",
      "financial_impact": "<cost of fixing now vs ignoring>",
      "urgency": "IMMEDIATE" | "SCHEDULE" | "MONITOR"
    }
  ],
  "recommendations": ["<action 1>", "<action 2>", "<action 3>"]
}

Rules:
- APPROVED: quality_score >= 80, no critical defects
- REVIEW: quality_score 50-79, minor defects only
- DEFECTIVE: quality_score < 50, or any critical/major defects
- Be specific and technical in all fields
- If no defects found, return empty defects array"""

# ── ANALYZE ──
@app.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):
    start = time.time()
    contents = await file.read()

    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if image is None:
        return JSONResponse({"error": "Invalid image"}, status_code=400)

    h, w = image.shape[:2]

    # Preprocess
    enhanced = preprocess_image(image)
    _, buffer = cv2.imencode(".jpg", enhanced, [cv2.IMWRITE_JPEG_QUALITY, 95])
    b64_image = base64.b64encode(buffer).decode("utf-8")

    # Call Groq Vision
    try:
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{b64_image}"
                            }
                        },
                        {
                            "type": "text",
                            "text": "Inspect this image for defects. Include damage progression and risk for every defect. Return only JSON."
                        }
                    ]
                }
            ],
            max_tokens=2000,
            temperature=0.1
        )

        raw = response.choices[0].message.content.strip()
        raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("```").strip()
        result = json.loads(raw)

    except Exception as e:
        return JSONResponse({"error": f"Analysis failed: {str(e)}"}, status_code=500)

    processing_time = round((time.time() - start) * 1000, 1)

    severity_counts = {"critical": 0, "major": 0, "minor": 0}
    for d in result.get("defects", []):
        sev = d.get("severity", "minor")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    save_inspection(file.filename or "camera_capture", result, processing_time)

    return {
        **result,
        "defect_count": len(result.get("defects", [])),
        "severity_counts": severity_counts,
        "image_size": {"width": w, "height": h},
        "processing_time_ms": processing_time,
    }

# ── HISTORY ──
@app.get("/history")
def get_history():
    conn = sqlite3.connect("visiq_history.db")
    c = conn.cursor()
    c.execute("""
        SELECT id, timestamp, filename, verdict, quality_score,
               defect_count, material_type, summary, processing_time_ms
        FROM inspections ORDER BY id DESC LIMIT 20
    """)
    rows = c.fetchall()
    conn.close()
    keys = ["id","timestamp","filename","verdict","quality_score",
            "defect_count","material_type","summary","processing_time_ms"]
    return [dict(zip(keys, r)) for r in rows]

# ── STATS ──
@app.get("/stats")
def get_stats():
    conn = sqlite3.connect("visiq_history.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM inspections")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM inspections WHERE verdict='APPROVED'")
    approved = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM inspections WHERE verdict='DEFECTIVE'")
    defective = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM inspections WHERE verdict='REVIEW'")
    review = c.fetchone()[0]
    c.execute("SELECT AVG(quality_score) FROM inspections")
    avg_score = c.fetchone()[0] or 0
    conn.close()
    return {
        "total": total,
        "approved": approved,
        "defective": defective,
        "review": review,
        "avg_score": round(avg_score, 1),
        "pass_rate": round((approved / total * 100) if total > 0 else 0, 1)
    }

# ── PDF EXPORT ──
@app.post("/export-pdf")
async def export_pdf(file: UploadFile = File(...)):
    contents = await file.read()
    data = json.loads(contents)
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=50, leftMargin=50,
                            topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle("title", fontSize=22,
                                  fontName="Helvetica-Bold",
                                  textColor=colors.HexColor("#1a1a2e"),
                                  spaceAfter=6)
    story.append(Paragraph("VISIQ Inspection Report", title_style))
    story.append(Paragraph(
        f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ParagraphStyle("sub", fontSize=10, textColor=colors.grey)))
    story.append(Spacer(1, 0.3*inch))

    verdict = data.get("verdict", "N/A")
    verdict_color = {
        "APPROVED": colors.green,
        "DEFECTIVE": colors.red,
        "REVIEW": colors.orange
    }.get(verdict, colors.grey)

    banner = Table(
        [[f"VERDICT: {verdict}  |  Score: {data.get('quality_score',0)}/100  |  Risk: {data.get('overall_risk','N/A')}"]],
        colWidths=[6.5*inch]
    )
    banner.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), verdict_color),
        ("TEXTCOLOR", (0,0), (-1,-1), colors.white),
        ("FONTNAME", (0,0), (-1,-1), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 13),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("TOPPADDING", (0,0), (-1,-1), 12),
        ("BOTTOMPADDING", (0,0), (-1,-1), 12),
    ]))
    story.append(banner)
    story.append(Spacer(1, 0.2*inch))

    h2 = ParagraphStyle("h2", fontSize=13, fontName="Helvetica-Bold", spaceAfter=6)
    story.append(Paragraph("Summary", h2))
    story.append(Paragraph(data.get("summary", ""), styles["Normal"]))
    story.append(Paragraph(f"Material: {data.get('material_type','N/A')}", styles["Normal"]))
    story.append(Paragraph(f"Remaining Life: {data.get('estimated_remaining_life','N/A')}", styles["Normal"]))
    story.append(Spacer(1, 0.2*inch))

    defects = data.get("defects", [])
    if defects:
        story.append(Paragraph("Defects Found", h2))
        for i, d in enumerate(defects):
            story.append(Paragraph(
                f"{i+1}. {d.get('label','?')} — {d.get('severity','?').upper()}",
                ParagraphStyle("dh", fontSize=11, fontName="Helvetica-Bold", spaceAfter=3)
            ))
            story.append(Paragraph(f"Location: {d.get('location','?')}", styles["Normal"]))
            story.append(Paragraph(f"Description: {d.get('description','?')}", styles["Normal"]))
            story.append(Paragraph(f"If ignored: {d.get('damage_if_ignored','?')}", styles["Normal"]))
            story.append(Paragraph(f"Timeline: {d.get('progression_timeline','?')}", styles["Normal"]))
            story.append(Paragraph(f"Financial Impact: {d.get('financial_impact','?')}", styles["Normal"]))
            story.append(Paragraph(
                f"Safety Risk: {d.get('safety_risk','?')} | Urgency: {d.get('urgency','?')}",
                styles["Normal"]
            ))
            story.append(Spacer(1, 0.15*inch))

    recs = data.get("recommendations", [])
    if recs:
        story.append(Paragraph("Recommendations", h2))
        for r in recs:
            story.append(Paragraph(f"• {r}", styles["Normal"]))

    doc.build(story)
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=visiq_report.pdf"}
    )

@app.get("/health")
def health():
    return {"status": "ok", "engine": "Groq Vision + OpenCV Preprocessing"}