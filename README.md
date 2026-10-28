# 📧 Bulk Email Sender

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4-38B2AC?style=flat&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![uv](https://img.shields.io/badge/managed%20with-uv-DE5FE9?style=flat)](https://github.com/astral-sh/uv)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A lightweight, self-hosted bulk email sender featuring a modern single-page dashboard. Send personalized emails with rich text formatting, file attachments, and optional CC/BCC — safeguarded by a pre-send verification modal.

---

## 📸 Overview & Workflow

``` 
┌─────────────────┐       ┌──────────────────────┐       ┌──────────────────────┐
│  Recipients     │  ──>  │  Pre-Send Modal      │  ──>  │  Async SMTP Dispatch │
│  (Name, email)  │       │  (Cross-check info)  │       │  (TLS / SSL)         │
└─────────────────┘       └──────────────────────┘       └──────────────────────┘
         │                                                           │
         ▼                                                           ▼
Personalization tags:                                      Personalized Inboxes:
• {{name}}                                                 • "Hey John..."
• {{email}}                                                • "Hey Sarah..."
```

---

## ✨ Features

- 🎨 **Rich Text Editor (Quill.js)** — Full WYSIWYG editor supporting bold, italics, headings, blockquotes, unordered/ordered lists, color highlighting, and clickable hyperlinks.
- 💌 **Dynamic Personalization** — Inject `{{name}}` and `{{email}}` anywhere in the email Subject and Body for tailored recipient outreach.
- 🛡️ **Pre-Send Confirmation Modal** — Review total recipient counts, CC/BCC targets, attachments, subject line, and rendered body HTML before dispatching.
- 📎 **Drag-and-Drop Attachments** — Upload multiple documents, PDFs, or images simultaneously with instant file tag previews and individual file removal.
- 📋 **Flexible Recipient Input** — Paste one recipient per line in either `Name, email@domain.com` or plain `email@domain.com` format.
- 👥 **Optional CC & BCC** — Clean collapsible section for comma-separated CC (visible header) and BCC (silent headerless delivery).
- 📱 **100% Fully Responsive** — Optimized breakpoints across mobile, tablet, and desktop viewports.
- ⚡ **Zero Database Overhead** — Pure in-memory dispatch powered by Python's asynchronous FastAPI and standard `smtplib`.

---

## 🚀 Quick Start Guide

### Prerequisites
Make sure you have [uv](https://docs.astral.sh/uv/) or Python 3.10+ installed.

### 1. Clone the Repository
```bash
git clone https://github.com/Mayuradlak123/bulk-email-sender.git
cd bulk-email-sender
```

### 2. Install Dependencies
Using **uv** (recommended — installs dependencies in seconds):
```bash
uv sync --no-install-project
```

*Or via traditional pip:*
```bash
pip install -r requirements.txt
```

### 3. Configure SMTP Credentials
Copy the example environment template:
```bash
cp .env.example .env
```

Open `.env` in your text editor and configure your credentials:
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
SENDER_NAME=Your Name or Organization
```

> ⚠️ **Security Notice:** Never commit your `.env` file to version control. The `.gitignore` included in this repo will protect it automatically.

### 4. Start the Application
```bash
uv run uvicorn main:app --reload
```

Visit **`http://localhost:8000`** in your browser.

---

## 🔑 How to Get a Gmail App Password

If you are using Gmail / Google Workspace:

1. Go to your **[Google Account Security Settings](https://myaccount.google.com/security)**.
2. Under *"How you sign in to Google"*, verify that **2-Step Verification** is turned ON.
3. Search for or click on **[App Passwords](https://myaccount.google.com/apppasswords)**.
4. Give your app a name (e.g. `Bulk Email Sender`) and click **Create**.
5. Copy the **16-character passcode** generated (without spaces) and paste it as `SMTP_PASSWORD` in your `.env`.

---

## ⚙️ Configuration for Other Providers

You can route emails through any standard SMTP server by updating `.env`:

| Provider | `SMTP_HOST` | `SMTP_PORT` | Notes |
|:---|:---|:---|:---|
| **Gmail** | `smtp.gmail.com` | `587` | Requires App Password |
| **Outlook / Office365** | `smtp.office365.com` | `587` | Requires SMTP enabled on account |
| **SendGrid** | `smtp.sendgrid.net` | `587` | User: `apikey`, Password: API Key |
| **Amazon SES** | `email-smtp.<region>.amazonaws.com` | `587` | Use SES SMTP credentials |
| **Mailgun** | `smtp.mailgun.org` | `587` | Use Mailgun SMTP credentials |

---

## 📝 Usage & Recipient Formatting

### Recipient List Format
Enter recipients one per line inside the textarea:
```text
Alice Johnson, alice@example.com
Bob Smith, bob@company.org
carol@domain.net
```
- If a name is provided before the comma, `{{name}}` resolves to that name.
- If only an email address is provided, `{{name}}` falls back to the email's username (e.g. `carol`).

### Personalization Example
- **Subject:** `Exclusive update for {{name}}!`
- **Body:**
  ```html
  <p>Hi <strong>{{name}}</strong>,</p>
  <p>We are reaching out to confirm your email: <em>{{email}}</em>.</p>
  ```

---

## 🗂️ Project Structure

```
bulk-email-sender/
├── main.py              # FastAPI backend (SMTP handler, template interpolation)
├── index.html           # Modern single-page UI (Tailwind CSS, Quill.js, Modal)
├── pyproject.toml       # uv dependency configuration
├── uv.lock              # Reproducible dependency lockfile
├── requirements.txt     # Standard pip requirements
├── .env.example         # Template for SMTP settings
├── .gitignore           # Prevents committing .env and virtual environments
└── README.md            # Project documentation
```

---

## 🛠️ Troubleshooting

- **`535 5.7.8 Username and Password not accepted` (Gmail):**  
  You must use a 16-character Google App Password, not your personal Google account password.
- **Port connection timeout (`SMTPConnectError`):**  
  Ensure port `587` (STARTTLS) or `465` (SSL) is open on your network and not blocked by local firewalls.
- **Recipient list format issues:**  
  Make sure each recipient is on a separate newline, using a comma `,` to separate name and email.

---

## 📄 License

This project is open-source and released under the [MIT License](LICENSE).
