import io
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def export_csv_bytes(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()

def export_pdf_bytes(title: str, df: pd.DataFrame, max_rows: int = 50) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    width, height = letter
    margin = 40
    y = height - margin
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin, y, title)
    y -= 20
    c.setFont("Helvetica", 9)

    rows = df.head(max_rows).to_dict(orient="records")
    col_names = list(df.columns)
    # header
    x = margin
    for col in col_names:
        c.drawString(x, y, str(col))
        x += 110
    y -= 15

    for r in rows:
        x = margin
        for col in col_names:
            text = str(r.get(col, ""))[:18]
            c.drawString(x, y, text)
            x += 110
        y -= 12
        if y < margin + 40:
            c.showPage()
            y = height - margin

    c.save()
    buf.seek(0)
    return buf.read()

def retention_suggestion(row: dict) -> str:
    # row can be a Series or dict
    p = row.get("churn_probability", row.get("churn_prob", 0))
    if p >= 0.8:
        return "Offer 0.75% rate reduction + RM callback"
    if row.get("delinquency_count", 0) >= 2:
        return "Invite to hardship program + payment plan"
    if row.get("complaints", 0) >= 2:
        return "Assign relationship manager and follow-up"
    if row.get("payment_inconsistency", 0) >= 3:
        return "Proactive outreach + payment coaching"
    return "Email personalized offers"
