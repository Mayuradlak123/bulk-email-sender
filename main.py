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
    candidates = [
        os.path.join(os.path.dirname(__file__), "index.html"),
        os.path.join(os.getcwd(), "index.html"),
        "index.html",
    ]
    for path in candidates:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>index.html not found</h1>", status_code=500)


EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def is_valid_email(email: str) -> bool:
    if not email or len(email) > 254:
        return False
    return bool(EMAIL_REGEX.match(email.strip()))


def is_domain_resolvable(domain: str) -> bool:
    """Check if the domain has active DNS records."""
    try:
        socket.getaddrinfo(domain, 25, proto=socket.IPPROTO_TCP)
        return True
    except Exception:
        try:
            socket.gethostbyname(domain)
            return True
        except Exception:
            return False


def parse_and_validate_recipients(raw_text: str) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    """
    Parses comma-separated, newline-separated, or semicolon-separated emails.
    Supports:
      - Name, email@domain.com
      - Name <email@domain.com>
      - a@b.com, c@d.com, e@f.com
    Validates RFC syntax, verifies active domain DNS, and removes duplicates.
    """
    entries = []
    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue
        # If line contains multiple '@' characters, split by commas or semicolons
        if line.count("@") > 1:
            tokens = re.split(r"[,;]+", line)
            for t in tokens:
                t = t.strip()
                if t:
                    entries.append(t)
        else:
            entries.append(line)

    valid_list = []
    skipped_list = []
    seen = set()

    for item in entries:
        item = item.strip().strip(",;")
        if not item:
            continue

        name = ""
        email = ""

        # Angle brackets: "Name <email@domain.com>"
        angle_match = re.search(r"^(.*?)\s*<([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)>", item)
        if angle_match:
            name = angle_match.group(1).strip().strip('"\'')
            email = angle_match.group(2).strip().lower()
        elif "," in item:
            parts = item.split(",", 1)
            p1, p2 = parts[0].strip(), parts[1].strip()
            if is_valid_email(p2):
                name = p1.strip('"\'')
                email = p2.lower()
            elif is_valid_email(p1):
                name = p2.strip('"\'')
                email = p1.lower()
            else:
                found = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", item)
                if found:
                    email = found[0].lower()
                    name = item.replace(found[0], "").strip(" ,;\"'<>")
        else:
            found = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", item)
            if found:
                email = found[0].lower()
                name = item.replace(found[0], "").strip(" ,;\"'<>")
            else:
                email = item.lower()

        if not email or not is_valid_email(email):
            skipped_list.append({"raw": item, "reason": "Invalid email format"})
            continue

        if email in seen:
            skipped_list.append({"raw": email, "reason": "Duplicate skipped"})
            continue
        seen.add(email)

        # Domain DNS active check
        domain = email.split("@", 1)[1]
        if not is_domain_resolvable(domain):
            skipped_list.append({"raw": email, "reason": f"Domain '{domain}' does not exist / inactive DNS"})
            continue

        if not name:
            name = email.split("@")[0]

        valid_list.append({"name": name, "email": email})

    return valid_list, skipped_list


# ── Validate endpoint ──────────────────────────────────────────────────────────
@app.post("/validate")
async def validate_recipients_endpoint(recipients: str = Form(...)):
    valid, skipped = parse_and_validate_recipients(recipients)
    return {
        "valid": valid,
        "valid_count": len(valid),
        "skipped": skipped,
        "skipped_count": len(skipped),
    }


# ── Send endpoint ──────────────────────────────────────────────────────────────
@app.post("/send")
async def send_emails(
    recipients: str = Form(...),
    subject: str = Form(...),
    body: str = Form(...),
    cc: Optional[str] = Form(default=None),
    bcc: Optional[str] = Form(default=None),
    attachments: Optional[List[UploadFile]] = File(default=None),
):
    """
    Send personalised bulk emails to verified, active recipients only.
    """
    valid_recipients, skipped_recipients = parse_and_validate_recipients(recipients)

    if not valid_recipients:
        raise HTTPException(
            status_code=400,
            detail=f"No active, valid email recipients found. Skipped: {len(skipped_recipients)} invalid entries."
        )

    # ── Parse CC / BCC ────────────────────────────────────────────────────────
    def parse_clean_emails(raw: Optional[str]) -> list:
        if not raw or not raw.strip():
            return []
        tokens = re.split(r"[,;]+", raw)
        return [t.strip().lower() for t in tokens if is_valid_email(t.strip())]

    cc_list  = parse_clean_emails(cc)
    bcc_list = parse_clean_emails(bcc)

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

    def get_smtp_connection():
        s = smtplib.SMTP(smtp_host, smtp_port, timeout=15)
        s.ehlo()
        s.starttls()
        s.login(smtp_user, smtp_password)
        return s

    server = None
    try:
        server = get_smtp_connection()

        for recipient in valid_recipients:
            try:
                # Personalise subject & body
                personalised_subject = subject.replace("{{name}}", recipient["name"]).replace("{{email}}", recipient["email"])
                personalised_body = body.replace("{{name}}", recipient["name"]).replace("{{email}}", recipient["email"])

                msg = MIMEMultipart()
                msg["From"]    = f"{sender_name} <{smtp_user}>"
                msg["To"]      = recipient["email"]
                msg["Subject"] = personalised_subject
                if cc_list:
                    msg["Cc"] = ", ".join(cc_list)

                msg.attach(MIMEText(personalised_body, "html"))

                # Attach files
                for att in attachment_data:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(att["content"])
                    encoders.encode_base64(part)
                    part.add_header("Content-Disposition", f'attachment; filename="{att["filename"]}"')
                    msg.attach(part)

                # Send directly to this specific recipient (+ cc/bcc)
                all_recipients = [recipient["email"]] + cc_list + bcc_list
                server.sendmail(smtp_user, all_recipients, msg.as_string())
                results.append({"email": recipient["email"], "status": "sent"})

            except Exception as e:
                errors.append({"email": recipient["email"], "error": str(e)})
                # Try reconnecting if server died during error
                try:
                    server.noop()
                except Exception:
                    try:
                        server = get_smtp_connection()
                    except Exception:
                        pass

        try:
            if server:
                server.quit()
        except Exception:
            pass

    except smtplib.SMTPAuthenticationError:
        raise HTTPException(status_code=401, detail="SMTP authentication failed. Check your credentials.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SMTP connection error: {str(e)}")

    return JSONResponse({
        "total": len(valid_recipients) + len(skipped_recipients),
        "valid": len(valid_recipients),
        "sent": len(results),
        "failed": len(errors),
        "skipped": len(skipped_recipients),
        "results": results,
        "errors": errors,
        "skipped_details": skipped_recipients,
    })


# ── Health check ───────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok"}

