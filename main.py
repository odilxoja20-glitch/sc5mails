import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from urllib.parse import unquote

app = FastAPI(
    title="SC5Mail API",
    description="Сервис автоматической рассылки писем через HTTP API Brevo",
    version="5.0"
)

# Настройки HTTP API Brevo
BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"
BREVO_API_KEY = os.getenv("BREVO_API_KEY")
SENDER_EMAIL = "servicecodes5@gmail.com"

def load_template():
    try:
        with open("scexample.txt", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return (
            "Zdrastvuyte, {Imya-chela}\n"
            "S vashim emailom pytautsa zaregistrirovatsa na sayt {Nazvanie-Kompanii}.\n"
            "Nam neoxodima podtverdit vashu Elektronnuyu Pochtu, prejde chem vy smojete sozdat akkaunt - voyti v akkaunt\n\n"
            "Kod-Podtverjdeniya: {Kod}\n"
            "Etot kod perestanet rabotat cherez {vremya-istekanie-koda}\n\n"
            "IP: {IP}, {ustroystvo}\n\n"
            "Esli eto ne vy, proignoriruyte eto soobshenie. Vozmojno kto to oshibsya e-mailom.\n"
            "S uvajeniem, {Nazvanie-Kompanii}\n\n"
            "Ispolzovan servis rassylki ServiceCode5 (SC5Mails)\n"
            "SC5 Web-site: www.sc5mails.space\n"
            "Tex. Podderjka sayta: {ssylka-na-tex-podderjku}"
        )

def send_via_brevo_api(to_email: str, subject: str, html_content: str, sender_name: str = "SC5Mail"):
    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json"
    }
    
    payload = {
        "sender": {"name": sender_name, "email": SENDER_EMAIL},
        "to": [{"email": to_email}],
        "subject": subject,
        "textContent": html_content
    }

    response = requests.post(BREVO_API_URL, json=payload, headers=headers)
    
    if response.status_code not in [200, 201, 202]:
        raise Exception(f"Ошибка API Brevo: {response.text}")
    return response.json()

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")

@app.get("/api/status", tags=["System"])
async def check_status():
    return {
        "status": "online",
        "service": "SC5Mail API",
        "version": "5.0",
        "method": "Brevo HTTP API (Port 443)"
    }

@app.get("/api/send_simple/{to_email}/{subject}/{message:path}", tags=["Email API"])
async def send_simple_email(to_email: str, subject: str, message: str):
    try:
        subject = unquote(subject)
        message = unquote(message)

        send_via_brevo_api(to_email, subject, message, sender_name="SC5Mail")

        return {"status": "success", "message": f"Письмо успешно отправлено на {to_email}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get(
    "/api/{company_name}/{code}/{to_email}/{subject}/{user_name}/{user_ip}/{device}/{support_link:path}/{expire_time}/done",
    summary="Отправка письма по шаблону",
    tags=["Email API"]
)
async def send_templated_email(
    company_name: str,
    code: str,
    to_email: str,
    subject: str,
    user_name: str,
    user_ip: str,
    device: str,
    support_link: str,
    expire_time: str
):
    try:
        company_name = unquote(company_name)
        subject = unquote(subject)
        user_name = unquote(user_name)
        device = unquote(device)
        support_link = unquote(support_link)
        expire_time = unquote(expire_time)

        template = load_template()

        body_text = template.format(
            **{
                "Imya-chela": user_name,
                "Nazvanie-Kompanii": company_name,
                "Kod": code,
                "vremya-istekanie-koda": expire_time,
                "IP": user_ip,
                "ustroystvo": device,
                "nazvanie-kompanii": company_name,
                "ssylka-na-tex-podderjku": support_link
            }
        )

        send_via_brevo_api(to_email, subject, body_text, sender_name=company_name)

        return {"status": "success", "message": f"Письмо по шаблону успешно отправлено на {to_email}"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
