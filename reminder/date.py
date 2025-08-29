import os
import logging
from datetime import datetime, timedelta

import gspread
from google.oauth2.service_account import Credentials
import pyttsx3
from apscheduler.schedulers.background import BackgroundScheduler

# ---------------- Logging ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# ---------------- Config ----------------
SERVICE_ACCOUNT_FILE = "credentials.json"  # Path to your service account key
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

SPREADSHEET_ID = "1nlf25Wk0wY5kzZz-5j2fVNJt9SpKl-Fiz3JEl2AUo2U"  # Replace with your Google Sheet ID
SHEET_NAME = "Sheet1"  # Replace if your sheet tab has a different name

LOOKAHEAD_DAYS = 3  # How many days ahead to remind
REMINDER_TIME = "12:30"  # Daily reminder time in HH:MM (24-hour, local time)

# ---------------- Speech Engine ----------------
engine = pyttsx3.init()
engine.setProperty("rate", 170)
engine.setProperty("volume", 1.0)

# ---------------- Functions ----------------
def speak(text: str):
    """Speak the given text aloud."""
    logging.info(f"Speaking reminder: {text}")
    engine.say(text)
    engine.runAndWait()

def fetch_sheet_rows():
    """Fetch rows from Google Sheets."""
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
    rows = sheet.get_all_records()
    logging.info(f"Fetched {len(rows)} rows from sheet")
    return rows

def check_and_speak_reminders():
    """Check sheet and speak due payment reminders."""
    rows = fetch_sheet_rows()
    now = datetime.now()
    today = now.date()
    lookahead = today + timedelta(days=LOOKAHEAD_DAYS)

    spoken_count = 0
    for row in rows:
        try:
            due_date = datetime.strptime(str(row["Due Date"]), "%d-%m-%Y").date()
        except ValueError:
            logging.warning(f"Skipping row with invalid due date: {row}")
            continue

        if today <= due_date <= lookahead:
            reminder_text = (
                f"Reminder: Payment of rupees {row['Amount']} "
                f"from {row['Name']} (Invoice {row['InvoiceID']}) "
                f"is due on {due_date.strftime('%d %B %Y')}."
            )
            speak(reminder_text)
            spoken_count += 1

    logging.info(f"Reminders spoken this run: {spoken_count}")

# ---------------- Main ----------------
def main():
    logging.info("Running initial reminder check...")
    check_and_speak_reminders()

    scheduler = BackgroundScheduler()
    hour, minute = map(int, REMINDER_TIME.split(":"))
    scheduler.add_job(check_and_speak_reminders, "cron", hour=hour, minute=minute)
    scheduler.start()
    logging.info(f"Scheduler started — daily reminders at {REMINDER_TIME}. Press Ctrl+C to exit.")

    try:
        import time
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logging.info("Scheduler stopped.")

if __name__ == "__main__":
    main()
