import os
import time
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
SERVICE_ACCOUNT_FILE = "credentials.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

SPREADSHEET_ID = "1nlf25Wk0wY5kzZz-5j2fVNJt9SpKl-Fiz3JEl2AUo2U"  # your Sheet ID
SHEET_NAME = "Sheet1"

LOOKAHEAD_DAYS = 3
REMINDER_TIME = "12:30"
COMPANY_NAME = "KREDMINT TECHNOLOGIES PVT. LTD."

# ---------------- Speech Engine ----------------
def speak(text: str):
    """Speak the given text aloud using a fresh engine instance each time."""
    logging.info(f"🔊 Speaking reminder...")
    engine = pyttsx3.init()
    engine.setProperty("rate", 170)
    engine.setProperty("volume", 1.0)
    engine.say(text)
    engine.runAndWait()
    engine.stop()

# ---------------- Google Sheets ----------------
def fetch_sheet_rows():
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
    rows = sheet.get_all_records()
    logging.info(f"Fetched {len(rows)} rows from sheet")
    return rows

# ---------------- Build Reminder Script ----------------
def build_script(customer, invoice_id, amount, due_date, status):
    if status == "today":
        return (f"Hello, this is the payment reminder assistant calling on behalf of {COMPANY_NAME}. "
                f"May I please speak with {customer}? "
                f"This is a gentle reminder that your payment of rupees {amount} for invoice {invoice_id} "
                f"is due today, {due_date}. You can pay securely via UPI, card, or online link. "
                "If you’ve already made this payment, please ignore this reminder. "
                "Thank you for your prompt action, we truly appreciate your business.")
    
    elif status == "upcoming":
        return (f"Hello, this is the payment reminder assistant calling on behalf of {COMPANY_NAME}. "
                f"May I please speak with {customer}? "
                f"I wanted to remind you that your payment of rupees {amount} for invoice {invoice_id} "
                f"is due on {due_date}. This is just an early reminder so you have time to plan your payment. "
                "If you’ve already completed the payment, please disregard this message. "
                "Thank you for your time and valued partnership with us.")
    
    elif status == "overdue":
        return (f"Hello, this is the payment reminder assistant from {COMPANY_NAME}. "
                f"May I please speak with {customer}? "
                f"Our records show that the payment of rupees {amount} for invoice {invoice_id}, "
                f"which was due on {due_date}, has not yet been received. "
                "If the payment has already been made, kindly ignore this message. "
                "If there is any delay, please let us know or allow me to connect you with our support team. "
                "We truly appreciate your cooperation and thank you for your business.")
    
    return ""

# ---------------- Calling Logic ----------------
def call_customer(name, message):
    logging.info(f"📞 Starting call to {name}")
    speak(message)
    logging.info(f"✅ Call finished for {name}")
    time.sleep(3)  # pause before next call

def process_reminders(reminders):
    spoken_count = 0
    for reminder in reminders:
        call_customer(reminder["customer"], reminder["message"])
        spoken_count += 1
    logging.info(f"📊 Reminders spoken this run: {spoken_count}")

# ---------------- Check Reminders ----------------
def check_and_speak_reminders():
    rows = fetch_sheet_rows()
    today = datetime.today().date()
    lookahead = today + timedelta(days=LOOKAHEAD_DAYS)

    reminders = []
    for row in rows:
        try:
            due_date = datetime.strptime(str(row["Due Date"]), "%d-%m-%Y").date()
        except ValueError:
            logging.warning(f"Skipping row with invalid due date: {row}")
            continue

        # classify
        if due_date == today:
            status = "today"
        elif today < due_date <= lookahead:
            status = "upcoming"
        elif due_date < today:
            status = "overdue"
        else:
            continue

        script = build_script(
            customer=row["Name"],
            invoice_id=row["InvoiceID"],
            amount=row["Amount"],
            due_date=due_date.strftime("%d %B %Y"),
            status=status,
        )
        if script:
            reminders.append({"customer": row["Name"], "message": script})

    # 🔑 Now process one by one like separate calls
    if reminders:
        process_reminders(reminders)
    else:
        logging.info("No reminders to speak today.")

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
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logging.info("Scheduler stopped.")

if __name__ == "__main__":
    main()
