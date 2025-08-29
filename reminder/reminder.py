# """
# reminder.py

# Reads Google Sheets and Google Calendar, matches upcoming payments,
# and speaks reminders locally via pyttsx3.

# Configuration section below — update values before running.
# """

# import os
# import logging
# import datetime
# from dateutil import parser as dateparser
# import pytz
# import pyttsx3
# from google.oauth2.service_account import Credentials
# from googleapiclient.discovery import build
# import gspread
# from apscheduler.schedulers.background import BackgroundScheduler
# from apscheduler.triggers.cron import CronTrigger
# from typing import List, Dict, Optional

# # ---------------- CONFIG ----------------
# CREDENTIALS_FILE = "credentials.json"          # path to service account JSON
# SPREADSHEET_ID = "1nlf25Wk0wY5kzZz-5j2fVNJt9SpKl-Fiz3JEl2AUo2U"    # paste your Google Sheet ID
# WORKSHEET_NAME = "Sheet1"                      # worksheet name
# CALENDAR_ID = "primary"                        # or specific calendar email
# LOOKAHEAD_DAYS = 3                             # how many days ahead to look for payments
# LOCAL_TZ = "Asia/Kolkata"                      # your local timezone for scheduling & comparisons
# SPEECH_RATE = 150                              # pyttsx3 speech rate (lower = slower)
# VOICE_ID = None                                # optional, leave None for default
# LOG_LEVEL = logging.INFO
# # -----------------------------------------

# logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s %(levelname)s %(message)s")
# logger = logging.getLogger(__name__)

# SCOPES = [
#     "https://www.googleapis.com/auth/calendar.readonly",
#     "https://www.googleapis.com/auth/spreadsheets.readonly",
# ]

# def init_google_services(credentials_file: str):
#     creds = Credentials.from_service_account_file(credentials_file, scopes=SCOPES)
#     calendar_service = build("calendar", "v3", credentials=creds)
#     gc = gspread.authorize(creds)
#     return calendar_service, gc

# def get_sheet_records(gc, spreadsheet_id: str, worksheet_name: str) -> List[Dict]:
#     sh = gc.open_by_key(spreadsheet_id)
#     worksheet = sh.worksheet(worksheet_name)
#     records = worksheet.get_all_records()
#     logger.info("Fetched %d rows from sheet", len(records))
#     return records

# def parse_date_safe(date_str: str, tzname: str) -> Optional[datetime.datetime]:
#     if not date_str:
#         return None
#     try:
#         dt = dateparser.parse(str(date_str))
#         if not dt.tzinfo:
#             # assume local tz if no tz present
#             local_tz = pytz.timezone(tzname)
#             dt = local_tz.localize(dt)
#         return dt.astimezone(pytz.utc)
#     except Exception as e:
#         logger.warning("Could not parse date '%s': %s", date_str, e)
#         return None

# def get_calendar_events(calendar_service, calendar_id: str, from_dt_utc: datetime.datetime, to_dt_utc: datetime.datetime) -> List[Dict]:
#     timeMin = from_dt_utc.isoformat (timespec="milliseconds").replace("+00:00", "Z")
#     timeMax = to_dt_utc.isoformat(timespec="milliseconds").replace("+00:00", "Z")
#     events_result = calendar_service.events().list(
#         calendarId=calendar_id,
#         timeMin=timeMin,
#         timeMax=timeMax,
#         singleEvents=True,
#         orderBy="startTime",
#         maxResults=250
#     ).execute()
#     items = events_result.get("items", [])
#     logger.info("Fetched %d calendar events between %s and %s", len(items), timeMin, timeMax)
#     return items

# def normalize_text(s: Optional[str]) -> str:
#     return (s or "").strip().lower()

# def match_event_to_record(event: Dict, records: List[Dict]) -> Optional[Dict]:
#     summary = normalize_text(event.get("summary", ""))
#     start_raw = event.get("start", {}).get("dateTime") or event.get("start", {}).get("date")
#     # 1) Try invoice id matching (if invoice id appears in summary)
#     for r in records:
#         invoice = normalize_text(str(r.get("InvoiceID", "")))
#         cal_key = normalize_text(str(r.get("CalendarKey", "")))
#         name = normalize_text(str(r.get("Name", "")))
#         if invoice and invoice in summary:
#             return r
#         if cal_key and cal_key in summary:
#             return r
#     # 2) Try name + date matching (compare dates)
#     try:
#         ev_dt = dateparser.parse(start_raw)
#         for r in records:
#             due_date_raw = r.get("Due Date") or r.get("DueDate") or r.get("Due_Date") or ""
#             r_dt = None
#             try:
#                 r_dt = dateparser.parse(str(due_date_raw))
#             except:
#                 r_dt = None
#             if r_dt:
#                 # compare date-only (local dates)
#                 if ev_dt.date() == r_dt.date():
#                     # also try name presence in summary
#                     if name and name in summary:
#                         return r
#                     # or just return on date match if only one candidate
#                     # BUT prefer a name match above
#                     # we'll choose this if no better found
#                     candidate = r
#                     return candidate
#     except Exception:
#         pass
#     return None

# def build_reminder_message(record: Dict, event: Dict) -> str:
#     name = record.get("Name") or "Customer"
#     amount = record.get("Amount") or record.get("Due Amount") or record.get("Amount Due") or ""
#     invoice = record.get("InvoiceID") or ""
#     due_date = record.get("Due Date") or event.get("start", {}).get("dateTime") or event.get("start", {}).get("date") or ""
#     # Format message
#     msg = f"Hello {name}. This is a friendly reminder that your payment"
#     if amount:
#         msg += f" of {amount}"
#     if invoice:
#         msg += f" for invoice {invoice}"
#     if due_date:
#         msg += f" is due on {due_date}."
#     else:
#         msg += " is due soon."
#     msg += " Please make the payment at your earliest convenience. Thank you for your time."
#     return msg

# def speak_message(message: str):
#     try:
#         engine = pyttsx3.init()
#         if VOICE_ID:
#             try:
#                 engine.setProperty('voice', VOICE_ID)
#             except Exception:
#                 logger.warning("Unable to set voice id %s", VOICE_ID)
#         engine.setProperty('rate', SPEECH_RATE)
#         logger.info("Speaking: %s", message)
#         engine.say(message)
#         engine.runAndWait()
#     except Exception as e:
#         logger.exception("TTS failed: %s", e)

# def process_and_speak(calendar_service, gc):
#     try:
#         # time window
#         now_local = datetime.datetime.now(pytz.timezone(LOCAL_TZ))
#         from_dt_local = now_local - datetime.timedelta(minutes=5)  # small buffer
#         to_dt_local = now_local + datetime.timedelta(days=LOOKAHEAD_DAYS)
#         from_dt_utc = from_dt_local.astimezone(pytz.utc)
#         to_dt_utc = to_dt_local.astimezone(pytz.utc)

#         records = get_sheet_records(gc, SPREADSHEET_ID, WORKSHEET_NAME)
#         events = get_calendar_events(calendar_service, CALENDAR_ID, from_dt_utc, to_dt_utc)

#         reminders_made = 0
#         for ev in events:
#             match = match_event_to_record(ev, records)
#             if match:
#                 message = build_reminder_message(match, ev)
#                 speak_message(message)
#                 reminders_made += 1
#             else:
#                 # Optionally, skip or create a generic message if event summary contains "payment" or "due"
#                 summary = (ev.get("summary") or "").lower()
#                 if "payment" in summary or "due" in summary:
#                     # generic fallback: extract event start date/time
#                     fallback_record = {"Name": "Customer", "Amount": "", "InvoiceID": ""}
#                     message = build_reminder_message(fallback_record, ev)
#                     speak_message(message)
#                     reminders_made += 1
#         logger.info("Reminders spoken this run: %d", reminders_made)
#     except Exception as e:
#         logger.exception("Error in process_and_speak: %s", e)

# def main():
#     if not os.path.exists(CREDENTIALS_FILE):
#         logger.error("Credentials file not found: %s", CREDENTIALS_FILE)
#         return

#     calendar_service, gc = init_google_services(CREDENTIALS_FILE)

#     # Run once on start
#     logger.info("Running initial reminder check...")
#     process_and_speak(calendar_service, gc)

#     # Schedule daily run at :11:12 AM local timezone
#     scheduler = BackgroundScheduler(timezone=LOCAL_TZ)
#     # CronTrigger: At 11:12 every day
#     trigger = CronTrigger(hour=11, minute=12)
#     scheduler.add_job(lambda: process_and_speak(calendar_service, gc),
#                       trigger=trigger,
#                       id="daily_payment_reminder")
#     scheduler.start()
#     logger.info("Scheduler started — daily reminders at 11:12 %s. Press Ctrl+C to exit.", LOCAL_TZ)

#     try:
#         # Keep the main thread alive.
#         while True:
#             # Sleep in small amounts so KeyboardInterrupt is responsive.
#             import time
#             time.sleep(1)
#     except (KeyboardInterrupt, SystemExit):
#         logger.info("Shutting down scheduler...")
#         scheduler.shutdown()

# if __name__ == "__main__":
#     main()


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
COMPANY_NAME = "KREDMINT TECHNOLOGIES PVT. LTD."

# ---------------- Speech Engine ----------------
engine = pyttsx3.init()
engine.setProperty("rate", 170)
engine.setProperty("volume", 1.0)

# def speak(text: str):
#     """Speak the given text aloud."""
#     logging.info(f"Speaking reminder: {text}")
#     engine.say(text)
#     engine.runAndWait()
# import time

# def speak(text: str):
#     """Speak the given text aloud using a fresh engine each time."""
#     logging.info(f"Speaking reminder: {text}")
#     engine = pyttsx3.init()
#     engine.setProperty("rate", 170)
#     engine.setProperty("volume", 1.0)
#     engine.say(text)
#     engine.runAndWait()
#     engine.stop()
#     time.sleep(1)  # give the system time before next reminder
def speak(text: str):
    """Speak the given text aloud using a fresh engine instance each time."""
    logging.info(f"Speaking reminder: {text}")  # ✅ Log each spoken reminder
    engine = pyttsx3.init()
    engine.setProperty("rate", 170)
    engine.setProperty("volume", 1.0)
    engine.say(text)
    engine.runAndWait()
    engine.stop()


# ---------------- Google Sheets ----------------
def fetch_sheet_rows():
    """Fetch rows from Google Sheets."""
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
    rows = sheet.get_all_records()
    logging.info(f"Fetched {len(rows)} rows from sheet")
    return rows

# ---------------- Build Reminder Script ----------------
def build_script(customer, invoice_id, amount, due_date, status):
    """Return a polite speaking script based on due status."""
    if status == "today":
        return (f"Hello, this is the payment reminder assistant calling on behalf of {COMPANY_NAME}. "
                f"May I please speak with {customer}? "
                f"This is a gentle reminder that your payment of rupees {amount} for invoice {invoice_id} "
                f"is due today, {due_date}. "
                "You can pay securely via UPI, card, or online link. "
                "If you’ve already made this payment, please ignore this reminder. "
                "Thank you for your prompt action, we truly appreciate your business.")
    
    elif status == "upcoming":
        return (f"Hello, this is the payment reminder assistant calling on behalf of {COMPANY_NAME}. "
                f"May I please speak with {customer}? "
                f"I wanted to remind you that your payment of rupees {amount} for invoice {invoice_id} "
                f"is due on {due_date}. "
                "This is just an early reminder so you have time to plan your payment. "
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

# ---------------- Check Reminders ----------------
# def check_and_speak_reminders():
#     """Check sheet and speak due payment reminders."""
#     rows = fetch_sheet_rows()
#     today = datetime.today().date()
#     lookahead = today + timedelta(days=LOOKAHEAD_DAYS)

#     spoken_count = 0
#     for row in rows:
#         try:
#             due_date = datetime.strptime(str(row["Due Date"]), "%d-%m-%Y").date()
#         except ValueError:
#             logging.warning(f"Skipping row with invalid due date: {row}")
#             continue

#         # classify status
#         if due_date == today:
#             status = "today"
#         elif today < due_date <= lookahead:
#             status = "upcoming"
#         elif due_date < today:
#             status = "overdue"
#         else:
#             continue

#         script = build_script(
#             customer=row["Name"],
#             invoice_id=row["InvoiceID"],
#             amount=row["Amount"],
#             due_date=due_date.strftime("%d %B %Y"),
#             status=status,
#         )
#         if script:
#             speak(script)
#             spoken_count += 1

#     logging.info(f"Reminders spoken this run: {spoken_count}")

import time

def check_and_speak_reminders():
    """Check sheet and speak due payment reminders."""
    rows = fetch_sheet_rows()
    today = datetime.today().date()
    lookahead = today + timedelta(days=LOOKAHEAD_DAYS)

    spoken_count = 0
    for row in rows:
        try:
            due_date = datetime.strptime(str(row["Due Date"]), "%d-%m-%Y").date()
        except ValueError:
            logging.warning(f"Skipping row with invalid due date: {row}")
            continue

        # classify status
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
            logging.info(f"📞 Starting call to {row['Name']}")
            speak(script)  # Speak one customer's reminder
            logging.info(f"✅ Call finished for {row['Name']}")
            spoken_count += 1

            # simulate hanging up before next call
            time.sleep(3)   # wait 3 seconds between calls (adjust if needed)

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
