import yfinance as yf
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# === CONFIGURATION ===
alertes = {
    "AAPL": 250.0,
    "MSFT": 280.0
}
email_from = os.environ.get('EMAIL_FROM')
email_to = os.environ.get('EMAIL_TO')
email_password = os.environ.get('EMAIL_PASSWORD')

# === FONCTION POUR ENVOYER LE MAIL ===
def envoyer_mail(symbole, prix_actuel, prix_seuil):
    sujet = f"🔔 Alerte Bourse : {symbole} est à {prix_actuel:.2f} $"
    message = f"L'action {symbole} est passée sous le seuil de {prix_seuil:.2f} $.\nPrix actuel : {prix_actuel:.2f} $"

    msg = MIMEMultipart()
    msg['From'] = email_from
    msg['To'] = email_to
    msg['Subject'] = sujet
    msg.attach(MIMEText(message, 'plain'))

    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login(email_from, email_password)
    server.sendmail(email_from, email_to, msg.as_string())
    server.quit()

# === CHECK DES PRIX ===
for symbole, seuil in alertes.items():
    action = yf.Ticker(symbole)
    prix_actuel = action.history(period='1d')['Close'].iloc[-1]

    if prix_actuel < seuil:
        envoyer_mail(symbole, prix_actuel, seuil)
        print(f"Alerte envoyée pour {symbole}")
    else:
        print(f"{symbole} est à {prix_actuel:.2f} $ > {seuil:.2f} $")
