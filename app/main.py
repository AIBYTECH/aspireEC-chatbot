from fastapi import FastAPI, Request, Depends, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr
import uuid
from app.session_manager import get_session, add_message
from app.chatbot_core import answer_query
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from dotenv import load_dotenv
from datetime import datetime
import json

load_dotenv()

app = FastAPI()

# CORS for iframe embedding
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for iframe embedding
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add security headers for iframe
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "ALLOW-FROM *"
    response.headers["Content-Security-Policy"] = "frame-ancestors *"
    return response

frontend_path = os.path.join(os.path.dirname(__file__), "..", "static")
app.mount("/static", StaticFiles(directory=frontend_path), name="static")

# Serve frontend
# app.mount("/static", StaticFiles(directory="static"), name="static")

# Email configuration
# ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
# SMTP_SERVER = os.getenv("SMTP_SERVER")
# SMTP_PORT = os.getenv("SMTP_PORT")
# SMTP_USERNAME = os.getenv("SMTP_USERNAME")
# SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# .env
ADMIN_EMAIL = "info.aibytech@gmail.com " # Replace with actual admin email
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "info.aibytech@gmail.com"  # Replace with your email
SMTP_PASSWORD = "znpt ppwy yvzi xomk"  # Replace with your app password

@app.get("/", response_class=HTMLResponse)
async def root():
    with open("static/form.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/chat", response_class=HTMLResponse)
async def chat_page():
    with open("static/index.html", "r") as f:
        return HTMLResponse(content=f.read())

# Request/response models
class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    messages: list

class FormData(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    studyLevel: str
    fieldOfInterest: str
    desiredCourse: str

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    messages = get_session(req.session_id)
    messages.append({"role": "user", "content": req.message})
    context, reply = answer_query(req.message, messages)
    messages.append({"role": "assistant", "content": reply})
    add_message(req.session_id, messages)

    # Count only user messages
    user_message_count = sum(1 for m in messages if m["role"] == "user")

    # If 5 user messages, send email
    if user_message_count % 10 == 0:
        try:
            # Format chat transcript
            transcript = ""
            for m in messages:
                transcript += f"{m['role'].capitalize()}: {m['content']}\n"

            msg = MIMEMultipart()
            msg['From'] = SMTP_USERNAME
            msg['To'] = ADMIN_EMAIL
            msg['Subject'] = f"Chat Transcript for Session {req.session_id} ({user_message_count} messages)"

            msg.attach(MIMEText(transcript, 'plain'))

            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(msg)
        except Exception as e:
            print(f"Error sending chat transcript: {str(e)}")

    return ChatResponse(response=reply, messages=messages)

@app.post("/submit-form")
async def submit_form(form_data: FormData):
    try:
        # Create email message
        msg = MIMEMultipart("alternative")
        msg['From'] = SMTP_USERNAME
        msg['To'] = ADMIN_EMAIL
        msg['Subject'] = "New Student Information Form Submission"

        # Create beautiful HTML email body
        html_body = f"""
        <html>
        <head>
          <style>
            .email-container {{
              font-family: 'Segoe UI', Arial, sans-serif;
              background: rgba(0,49,53,0.9);
              padding: 24px;
              border-radius: 12px;
              max-width: 580px;
              margin: 0 auto;
              box-shadow: 0 2px 12px rgba(52,152,219,0.08);
            }}
            .email-title {{
              color: #FFFFFF;
              font-size: 1.3rem;
              font-weight: bold;
              margin-bottom: 18px;
              text-align: center;
            }}
            .email-table {{
              width: 100%;
              border-collapse: collapse;
              background: #fff;
              border-radius: 8px;
              overflow: hidden;
            }}
            .email-table td {{
              padding: 10px 14px;
              border-bottom: 1px solid #f0f0f0;
              font-size: 1rem;
            }}
            .email-table tr:last-child td {{
              border-bottom: none;
            }}
            .label {{
              color: #34495e;
              font-weight: 500;
              width: 40%;
              background: #f7fbff;
            }}
            .value {{
              color: #2d3436;
              width: 60%;
            }}
          </style>
        </head>
        <body>
          <div class="email-container">
            <div class="email-title">New Student Information Form Submission</div>
            <table class="email-table">
              <tr><td class="label">Name</td><td class="value">{form_data.name}</td></tr>
              <tr><td class="label">Email</td><td class="value">{form_data.email}</td></tr>
              <tr><td class="label">Phone</td><td class="value">{form_data.phone or 'Not provided'}</td></tr>
              <tr><td class="label">Level of Study</td><td class="value">{form_data.studyLevel}</td></tr>
              <tr><td class="label">Field of Interest</td><td class="value">{form_data.fieldOfInterest}</td></tr>
              <tr><td class="label">Desired Course</td><td class="value">{form_data.desiredCourse}</td></tr>
            </table>
          </div>
        </body>
        </html>
        """

        # Attach HTML and plain text fallback
        plain_body = f"""
        New Student Information Form Submission:\n\nName: {form_data.name}\nEmail: {form_data.email}\nPhone: {form_data.phone or 'Not provided'}\nLevel of Study: {form_data.studyLevel}\nField of Interest: {form_data.fieldOfInterest}\nDesired Course: {form_data.desiredCourse}
        """
        msg.attach(MIMEText(plain_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))

        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)

        return JSONResponse(content={"success": True, "message": "Form submitted successfully"})
    except Exception as e:
        print(f"Error submitting form: {str(e)}")  # Add logging
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Error submitting form: {str(e)}"}
        )
