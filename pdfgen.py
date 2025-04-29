# pdfgen.py
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet
import io
from google import genai

def create_referral_pdf(
    img,                        # PIL Image
    prob: float,
    severity: str,
    tag: str,
    patient_name: str,
    genai_client: genai.Client,
) -> bytes:
    """Return a one-page PDF (bytes)."""
    # 1) Build prompt & call Gemini
    prompt = f"""
You are an empathetic medical assistant. Draft a concise referral email
(≤250 words) from the patient to their dermatologist.
Include:
• Date: {datetime.utcnow():%Y-%m-%d}
• Patient name: {patient_name}
• Body area: {tag}
• AI estimate: {prob:.1%} chance melanoma ({severity})
Ask politely for next-step guidance and an appointment.
Tone: professional, clear.
"""
    letter = genai_client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[prompt],
        config=genai.types.GenerateContentConfig(temperature=0.3),
    ).text

    # 2) Convert PIL -> PNG in memory
    img_buf = io.BytesIO()
    img.save(img_buf, format="PNG")
    img_buf.seek(0)

    # 3) Build PDF
    out = io.BytesIO()
    doc = SimpleDocTemplate(out)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Melo – Analysis Results", styles["Title"]),
        Paragraph(letter.replace("\n", "<br/>"), styles["Normal"]),
        Paragraph("Image:", styles["Heading3"]),
        RLImage(img_buf, width=240, height=240),    # just pass the BytesIO
    ]
    doc.build(story)

    return out.getvalue()
