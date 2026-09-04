import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from urllib.parse import unquote

app = FastAPI(
    title="SC5Mail API",
    description="Сервис автоматической рассылки писем и OTP-кодов",
    version="5.0"
)

EMAIL = "servicecodes5@gmail.com"
PASS = os.environ.get("PASS")

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
            "SC5 Web-site: sc5mails.site\n"
            "Tex. Podderjka sayta: {ssylka-na-tex-podderjku}"
        )

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")

@app.get("/api/status", tags=["System"])
async def check_status():
    return {
        "status": "online",
        "service": "SC5Mail API",
        "version": "5.0",
        "smtp_provider": "gmail"
    }

@app.get("/api/send_simple/{to_email}/{subject}/{message:path}", tags=["Email API"])
async def send_simple_email(to_email: str, subject: str, message: str):
    try:
        subject = unquote(subject)
        message = unquote(message)

        msg = MIMEMultipart()
        msg['From'] = f"SC5Mail <{EMAIL}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain', 'utf-8'))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL, PASS)
            server.send_message(msg)

        return {"status": "success", "message": f"Простое письмо отправлено на {to_email}"}
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

        msg = MIMEMultipart()
        msg['From'] = f"{company_name} <{EMAIL}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body_text, 'plain', 'utf-8'))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL, PASS)
            server.send_message(msg)

        return {"status": "success", "message": f"Письмо успешно отправлено на {to_email}"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))