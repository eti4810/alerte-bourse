import yfinance as yf
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# === CONFIGURATION ===
alertes = {
    "ASML.AS": 530.0,
    "MC.PA": 450.0,
    "PUB.PA": 170.0,
    "AIR.PA": 120.0,
    "CAP.PA": 110.0,
    "LR.PA": 80.0,
    "DSY.PA": 32.0,
    "GTT.PA": 120.0,
    "SAN.PA": 185.0
}

email_from = os.environ.get('EMAIL_FROM')
email_to = os.environ.get('EMAIL_TO')
email_password = os.environ.get('EMAIL_PASSWORD')

# === Fonction pour envoyer un e-mail groupé ===
def envoyer_mail_alerte(liste_alertes):
    sujet = f"🔔 Alerte Bourse - {len(liste_alertes)} action(s) sous seuil"
    message = "Voici les alertes détectées aujourd'hui :\n\n"

    for symbole, prix_actuel, seuil in liste_alertes:
        message += f"- {symbole} est à {prix_actuel:.2f} € < seuil {seuil:.2f} €\n"

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
liste_alertes = []

for symbole, seuil in alertes.items():
    action = yf.Ticker(symbole)

    try:
        prix_actuel = action.history(period='1d')['Close'].iloc[-1]
    except Exception as e:
        print(f"⚠️ Erreur pour {symbole} : {e}")
        continue

    if prix_actuel < seuil:
        liste_alertes.append((symbole, prix_actuel, seuil))
        print(f"🔔 {symbole} est à {prix_actuel:.2f} € < {seuil:.2f} € ✅")
    else:
        print(f"{symbole} est à {prix_actuel:.2f} € > {seuil:.2f} €")

# Envoi unique si au moins une alerte
if liste_alertes:
    envoyer_mail_alerte(liste_alertes)
    print(f"✅ Email envoyé avec {len(liste_alertes)} alerte(s)")
else:
    print("📭 Aucune alerte aujourd'hui")
