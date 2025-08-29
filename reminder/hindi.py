import os
import time
import logging
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials
from apscheduler.schedulers.background import BackgroundScheduler
from gtts import gTTS
import pygame
import tempfile

# ---------------- Logging ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# ---------------- Config ----------------
SERVICE_ACCOUNT_FILE = "credentials.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

SPREADSHEET_ID = "1nlf25Wk0wY5kzZz-5j2fVNJt9SpKl-Fiz3JEl2AUo2U"
SHEET_NAME = "Sheet1"

LOOKAHEAD_DAYS = 3
REMINDER_TIME = "12:30"
COMPANY_NAME = "क्रेडमिंट टेक्नोलॉजीज प्राइवेट लिमिटेड"

# ---------------- Speech Engine ----------------
def speak(text: str,speed: float = 1.5):
    """
    Speak the given text aloud in natural Indian Hindi-English (Hinglish).
    """
    logging.info(" Speaking reminder...")
    try:
       # tts = gTTS(text=text, lang="hi", tld="co.in")
        tts = gTTS(text=text, lang="hi", tld="co.in", slow=False)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            temp_file = fp.name
            tts.save(temp_file)
        pygame.mixer.init(frequency=int(22050 * speed))

        pygame.mixer.music.load(temp_file)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.05)
        pygame.mixer.quit()
        os.remove(temp_file)
    except Exception as e:
        logging.error(f" Speech error: {e}")


# ---------------- Google Sheets ----------------
def fetch_sheet_rows():
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
    rows = sheet.get_all_records()
    logging.info(f"Fetched {len(rows)} rows from sheet")
    return rows

# ---------------- Build Reminder Script ----------------
# def build_script(customer, invoice_id, amount, due_date, status):
#     """
#     Return a polite, friendly Hindi+English reminder for the customer.
#     Female conversational tone.
#     """
#     if status == "today":
#         return (
#             f"नमस्ते {customer} जी। मैं {COMPANY_NAME} की ओर से बोल रही हूँ। "
#             f"आपकी invoice {invoice_id} की payment, {amount} रुपये, आज, {due_date} को due है। "
#             "कृपया यूपीआई, कार्ड या ऑनलाइन लिंक से payment कर दें। "
#             "अगर आपने पहले ही payment कर दिया है, तो कोई बात नहीं, इस संदेश को ignore कर दीजिए। "
#             "धन्यवाद। आपका सहयोग हमारे लिए बहुत महत्वपूर्ण है।"
#         )

#     elif status == "upcoming":
#         return (
#             f"नमस्ते {customer} जी। यह {COMPANY_NAME} की payment reminder call है। "
#             f"आपकी invoice {invoice_id} की payment, {amount} , {due_date} को due है। "
#             "बस आपको gentle reminder देना था ताकि आप आराम से payment plan कर सकें। "
#             "अगर payment already कर दिया है, तो कृपया इस message को ignore कर दें। "
#             "हम आपके business की बहुत कद्र करते हैं।" 
#         )

#     elif status == "overdue":
#         return (
#             f"नमस्ते {customer} जी। मैं {COMPANY_NAME} से बोल रही हूँ। "
#             f"हमारे records के अनुसार invoice {invoice_id} की {amount} रुपये की payment, {due_date} को due थी, "
#             "और अभी तक receive नहीं हुई है। "
#             "अगर आपने already payment कर दिया है तो ठीक है, ignore कर दीजिए। "
#             "अगर payment में कोई समस्या है, तो कृपया हमें inform करें या support team से बात कर लें। "
#             "आपके सहयोग के लिए हम बहुत आभारी हैं।"
#         )

#     return ""

def build_script(customer, invoice_id, amount, due_date, status):
    """
    Friendly, natural Hindi+English payment reminder in female voice style.
    Short, clear, and optimized for fast gTTS playback.
    """
    if status == "today":
        return (
          f"नमस्ते {customer} जी, मैं {COMPANY_NAME} से बोल रही हूँ। "
          f"आपका {amount} रुपए का payment आज {due_date} को बकाया है। "
           "कृपया समय पर भुगतान करें, या हमारे ऐप से तुरंत payment कर सकते हैं, "
           "जो प्लेस्टोर और ऐप स्टोर पर उपलब्ध है। "
           "अगर आपने पहले ही payment कर दिया है, तो इस message को ignore कर दीजिए। "
           "धन्यवाद, आपका सहयोग हमारे लिए बहुत मायने रखता है।"
        )

    elif status == "upcoming":
        return (
            f"नमस्ते {customer} जी। मैं {COMPANY_NAME} से बोल रही हूँ। "
            f"आपका {amount} रुपए का payment {due_date} को due है। "
            "यह सिर्फ एक friendly payment reminder है ताकि आप समय पर payment कर सकें। "
            "आप हमारे ऐप से भी जल्दी payment कर सकते हैं। "
            "जिसे प्लेस्टोर या ऐप स्टोर से डाउनलोड कर सकते हैं। "
            "अगर आपने पहले ही payment कर दिया है, तो कोई बात नहीं। "
            "धन्यवाद, आपका सहयोग हमारे लिए बहुत महत्वपूर्ण है।"
        )

    elif status == "overdue":
        return (
            f"नमस्ते {customer} जी। मैं {COMPANY_NAME} से बोल रही हूँ। "
            f"हमारे records के अनुसार आपका {amount} रुपए का payment {due_date} को due था और अभी तक receive नहीं हुआ है। "
            "कृपया जल्द से जल्द भुगतान करें, या हमारे ऐप से तुरंत payment कर सकते हैं। "
            "जिसे प्लेस्टोर या ऐप स्टोर से डाउनलोड कर सकते हैं। "
            "अगर आपने पहले ही payment कर दिया है, तो कोई बात नहीं। "
            "धन्यवाद, आपका सहयोग हमारे लिए बहुत महत्वपूर्ण है।"
        )

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

