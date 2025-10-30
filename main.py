from fastapi import FastAPI, Form
from fastapi.responses import FileResponse, HTMLResponse
import random
import smtplib
import os
from datetime import datetime, timedelta

app = FastAPI()

user_info = {}

def generate_otp():
    return ''.join(str(random.randint(0, 9)) for _ in range(6))

def send_otp(user_email):
    otp = generate_otp()
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASS"))  # from Render env vars

        message = f"""Subject: Your One-Time Password (OTP)

Dear User,

Your verification code is: {otp}

Use this OTP to complete your verification process.
It will remain valid for 10 minutes.
For your safety, do not share this code with anyone.

— Admin
"""
        server.sendmail(os.getenv("EMAIL_USER"), user_email, message.encode('utf-8'))
        print(f"✅ OTP sent to {user_email}: {otp}")
    except Exception as e:
        print("❌ Error sending email:", e)
    finally:
        server.quit()
    return otp


@app.post("/verify")
def enter_email(email: str = Form(...)):
    curr_time = datetime.now()
    expiry = curr_time + timedelta(minutes=10)
    otp = send_otp(email)
    user_info[email] = {"otp": otp, "expiry": expiry}

    try:
        with open("otp.html", "r", encoding="utf-8") as f:
            html = f.read().replace("{{email}}", email)
        return HTMLResponse(content=html)
    except Exception as e:
        print("❌ Error loading otp.html:", e)
        return {"message": "Server error — unable to load OTP page."}


@app.post("/otp-verification")
def verify_otp(email: str = Form(...), otp_input: str = Form(...)):
    if email not in user_info:
        return {"message": "Email not found. Please request OTP again."}

    record = user_info[email]
    if datetime.now() > record["expiry"]:
        return {"message": "OTP expired."}
    if otp_input != record["otp"]:
        return {"message": "Wrong OTP."}
    return FileResponse("temp.html")


@app.get("/")
def home():
    return FileResponse("index.html")
