import requests
import os
import smtplib
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# === CONFIGURATION ===
URL = "https://jobs.servier.com/search/?locationsearch=suresnes"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ServierScraper/1.0)"
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
    day, month_str, year = date_str.split()
    return datetime(int(year), MONTHS_FR[month_str], int(day))


# === SCRAPING ===
def fetch_jobs() -> List[Dict[str, str]]:
    response = requests.get(URL, headers=HEADERS, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    jobs = []

    for job in soup.select("li.job-tile"):
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

    # 🔽 TRI PAR DATE DÉCROISSANTE
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


if __name__ == "__main__":
    main()
