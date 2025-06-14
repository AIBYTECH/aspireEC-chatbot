from fastapi import FastAPI, Request, Depends, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr
import uuid
from app.session_manager import get_session, add_message
from app.chatbot_core import initialize_resources, answer_query
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from dotenv import load_dotenv

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
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

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

# Load resources
chunks, vectorizer = initialize_resources()

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    messages = get_session(req.session_id)
    messages.append({"role": "user", "content": req.message})
    context, reply = answer_query(req.message, messages, chunks, vectorizer)
    messages.append({"role": "assistant", "content": reply})
    add_message(req.session_id, messages)
    return ChatResponse(response=reply, messages=messages)

@app.post("/submit-form")
async def submit_form(form_data: FormData):
    try:
        # Create email message
        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = ADMIN_EMAIL
        msg['Subject'] = "New Student Information Form Submission"

        # Create email body
        body = f"""
        New Student Information Form Submission:
        
        Name: {form_data.name}
        Email: {form_data.email}
        Phone: {form_data.phone or 'Not provided'}
        Level of Study: {form_data.studyLevel}
        Field of Interest: {form_data.fieldOfInterest}
        Desired Course: {form_data.desiredCourse}
        """

        msg.attach(MIMEText(body, 'plain'))

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
