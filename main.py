import os
import smtplib
import traceback
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional

from fastapi import FastAPI, Form, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Bulk Email Sender")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Serve index.html at "/" ────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def root():
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


# ── Send endpoint ──────────────────────────────────────────────────────────────
@app.post("/send")
async def send_emails(
    recipients: str = Form(...),          # newline-separated "Name, email" or just "email"
    subject: str = Form(...),
    body: str = Form(...),                # supports {{name}} {{email}} placeholders
    cc: Optional[str] = Form(default=None),   # comma-separated CC addresses
    bcc: Optional[str] = Form(default=None),  # comma-separated BCC addresses
    attachments: Optional[List[UploadFile]] = File(default=None),
):
    """
    Send personalised bulk emails.

    recipients format (one per line):
        John Doe | john@example.com
        jane@example.com          <- name defaults to email prefix
    """

    # ── Parse recipients ────────────────────────────────────────────────────
    lines = [l.strip() for l in recipients.splitlines() if l.strip()]
    parsed = []
    for line in lines:
        if "," in line:
            parts = line.split(",", 1)
            name = parts[0].strip()
            email = parts[1].strip()
        else:
            email = line.strip()
            name = email.split("@")[0]
        if email:
            parsed.append({"name": name, "email": email})

    if not parsed:
        raise HTTPException(status_code=400, detail="No valid recipients found.")

    # ── Parse CC / BCC ────────────────────────────────────────────────────────
    def parse_simple_emails(raw: Optional[str]) -> list:
        if not raw or not raw.strip():
            return []
        return [e.strip() for e in raw.split(",") if e.strip()]

    cc_list  = parse_simple_emails(cc)
    bcc_list = parse_simple_emails(bcc)

    # ── Read attachment bytes once ──────────────────────────────────────────
    attachment_data = []
    if attachments:
        for att in attachments:
            if att.filename:
                content = await att.read()
                attachment_data.append({"filename": att.filename, "content": content, "content_type": att.content_type})

    # ── SMTP config ─────────────────────────────────────────────────────────
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    sender_name = os.getenv("SENDER_NAME", smtp_user)

    if not smtp_user or not smtp_password:
        raise HTTPException(status_code=500, detail="SMTP credentials not configured. Check your .env file.")

    results = []
    errors = []

    try:
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.ehlo()
        server.starttls()
        server.login(smtp_user, smtp_password)

        for recipient in parsed:
            try:
                # Personalise subject & body
                personalised_subject = subject.replace("{{name}}", recipient["name"]).replace("{{email}}", recipient["email"])
                personalised_body = body.replace("{{name}}", recipient["name"]).replace("{{email}}", recipient["email"])

                msg = MIMEMultipart()
                msg["From"]    = f"{sender_name} <{smtp_user}>"
                msg["To"]      = recipient["email"]
                msg["Subject"] = personalised_subject
                if cc_list:
                    msg["Cc"] = ", ".join(cc_list)   # visible CC header
                # BCC: no header — addresses go only into sendmail's recipient list

                msg.attach(MIMEText(personalised_body, "html"))

                # Attach files
                for att in attachment_data:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(att["content"])
                    encoders.encode_base64(part)
                    part.add_header("Content-Disposition", f'attachment; filename="{att["filename"]}"')
                    msg.attach(part)

                # Build full recipient list: To + CC + BCC
                all_recipients = [recipient["email"]] + cc_list + bcc_list
                server.sendmail(smtp_user, all_recipients, msg.as_string())
                results.append({"email": recipient["email"], "status": "sent"})

            except Exception as e:
                errors.append({"email": recipient["email"], "error": str(e)})

        server.quit()

    except smtplib.SMTPAuthenticationError:
        raise HTTPException(status_code=401, detail="SMTP authentication failed. Check your credentials.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SMTP connection error: {str(e)}")

    return JSONResponse({
        "total": len(parsed),
        "sent": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors,
    })


# ── Health check ───────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok"}
