import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

def send_email_alert(product_name, remaining_days, depletion_date, stock, sender_email, sender_password, receiver_email):
    if sender_email == "your_email@gmail.com":
        return "ℹ️ Email sending skipped: configure your credentials in the sidebar."

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = f"⚠️ [PURCHASE ALERT] - {product_name} running out!"

    body = f"""
    Attention, the system has detected a critical replenishment need:
    
    Product: {product_name}
    Current Stock: {stock} units
    Estimated Remaining Days: {remaining_days} days
    Expected Depletion Date: {depletion_date}
    
    Please generate a new purchase order immediately.
    """
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        return f"📧 Alert email successfully sent to {receiver_email}!"
    except Exception as e:
        return f"❌ Failed to send email: {e}"