import requests
import os
import smtplib
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# === CONFIGURATION ===
URL = "https://jobs.servier.com/search/?createNewAlert=false&q=&locationsearch=suresnes&optionsFacetsDD_country=&optionsFacetsDD_lang=&optionsFacetsDD_customfield1=&optionsFacetsDD_customfield3=&optionsFacetsDD_customfield4="

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ServierScraper/1.0)",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
}

email_from = os.environ.get("EMAIL_FROM")
email_to = os.environ.get("EMAIL_TO")
email_password = os.environ.get("EMAIL_PASSWORD")

MONTHS_FR = {
    "janv.": 1, "févr.": 2, "mars": 3, "avr.": 4,
    "mai": 5, "juin": 6, "juil.": 7, "août": 8,
    "sept.": 9, "oct.": 10, "nov.": 11, "déc.": 12
}

# === UTILITAIRES ===
def parse_french_date(date_str: str) -> datetime:
    # Ex: "21 janv. 2026"
    day, month_str, year = date_str.split()
    return datetime(int(year), MONTHS_FR[month_str], int(day))


def looks_like_login_page(html: str, final_url: str) -> bool:
    """
    Détection robuste : uniquement des indices forts (pas de simple mot-clé "connexion").
    """
    u = (final_url or "").lower()
    if any(x in u for x in ["login", "sso", "signin", "auth"]):
        return True

    soup = BeautifulSoup(html, "html.parser")

    # Indice très fort : champ mot de passe
    if soup.select_one('input[type="password"]'):
        return True

    # Indice fort : formulaire mentionnant mot de passe
    for f in soup.select("form"):
        txt = f.get_text(" ", strip=True).lower()
        if "mot de passe" in txt or "password" in txt:
            return True

    return False


def save_debug_html(html: str, filename: str = "debug_servier.html"):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)


# === SCRAPING ===
def fetch_jobs() -> List[Dict[str, str]]:
    session = requests.Session()

    # On bloque les redirects pour détecter un renvoi vers login/SSO
    resp = session.get(URL, headers=HEADERS, timeout=20, allow_redirects=False)

    if resp.status_code in (301, 302, 303, 307, 308):
        location = resp.headers.get("Location", "")
        raise RuntimeError(f"Redirection détectée (probable login/SSO) vers: {location}")

    resp.raise_for_status()

    # Vérifie si c'est une vraie page de login
    if looks_like_login_page(resp.text, resp.url):
        save_debug_html(resp.text)
        raise RuntimeError("La page récupérée ressemble à une page de connexion (login/SSO). "
                           "HTML sauvegardé dans debug_servier.html")

    soup = BeautifulSoup(resp.text, "html.parser")

    # Si aucun job tile, on sauvegarde le HTML pour comprendre (JS, blocage, changement DOM, etc.)
    tiles = soup.select("li.job-tile")
    if not tiles:
        save_debug_html(resp.text)
        raise RuntimeError("Aucun 'li.job-tile' trouvé. HTML sauvegardé dans debug_servier.html "
                           "(probable chargement JS, blocage anti-bot, ou structure HTML modifiée).")

    jobs = []
    for job in tiles:
        title_tag = job.select_one("a.jobTitle-link")
        date_tag = job.select_one('div[id$="-desktop-section-date-value"]')

        if not title_tag or not date_tag:
            continue

        date_str = date_tag.get_text(strip=True)

        jobs.append({
            "title": title_tag.get_text(strip=True),
            "date": date_str,
            "date_dt": parse_french_date(date_str)
        })

    # TRI PAR DATE DÉCROISSANTE
    jobs.sort(key=lambda x: x["date_dt"], reverse=True)

    return jobs


# === EMAIL ===
def envoyer_mail_jobs(jobs: List[Dict[str, str]]):
    sujet = f"📢 Offres Servier – Suresnes ({len(jobs)} postes)"
    message = "Voici la liste des offres actuellement publiées (triées par date) :\n\n"

    for job in jobs:
        message += f"- {job['date']} | {job['title']}\n"

    message += f"\nLien direct : {URL}"

    msg = MIMEMultipart()
    msg["From"] = email_from
    msg["To"] = email_to
    msg["Subject"] = sujet
    msg.attach(MIMEText(message, "plain"))

    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login(email_from, email_password)
    server.sendmail(email_from, email_to, msg.as_string())
    server.quit()


# === MAIN ===
def main():
    jobs = fetch_jobs()

    if jobs:
        envoyer_mail_jobs(jobs)
        print(f"✅ Email envoyé avec {len(jobs)} offre(s)")
    else:
        print("📭 Aucune offre trouvée")
