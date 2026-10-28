# 📧 Bulk Email Sender

Send personalized bulk emails with rich text, attachments, CC/BCC — all from a beautiful single-page UI.

Built with **FastAPI** + **Quill.js** + **Tailwind CSS**, managed with **uv**.

---

## ✨ Features

- 🎨 **Rich text editor** — bold, italic, headings, links, colors, lists (Quill.js)
- 🧑‍🤝‍🧑 **Bulk recipients** — paste one per line as `Name, email` or just `email`
- 💌 **Personalized emails** — use `{{name}}` and `{{email}}` in subject & body
- 📎 **Drag-and-drop attachments** — multiple files supported
- 📋 **CC / BCC** — optional, comma-separated
- ✅ **Confirmation modal** — review everything before sending
- 📱 **Fully responsive** — works on mobile, tablet, and desktop

---

## 🚀 Quick Start

### 1. Install [uv](https://docs.astral.sh/uv/)
```bash
pip install uv
```

### 2. Clone & install dependencies
```bash
git clone https://github.com/Mayuradlak123/bulk-email-sender.git
cd bulk-email-sender
uv sync --no-install-project
```

### 3. Configure SMTP credentials
```bash
cp .env.example .env
# Edit .env with your Gmail credentials
```

`.env` file:
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password   # Gmail App Password
SENDER_NAME=Your Name
```

> **Gmail**: Go to Google Account → Security → 2-Step Verification → **App Passwords**

### 4. Run
```bash
uv run uvicorn main:app --reload
```

Open **http://localhost:8000** 🎉

---

## 📋 Recipient Format

```
John Doe, john@example.com
Jane Smith, jane@example.com
bob@example.com
```

---

## 🗂️ Project Structure

```
bulk-email-sender/
├── main.py          # FastAPI backend
├── index.html       # Single-page UI
├── pyproject.toml   # uv project config
├── .env.example     # SMTP config template
└── .gitignore
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI, Python `smtplib` |
| Frontend | HTML, Tailwind CSS (CDN), Quill.js |
| Package Manager | uv |
| Email | SMTP (Gmail / any provider) |
