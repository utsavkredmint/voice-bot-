import asyncio
import io
import sys
import traceback
import logging
import pyaudio
import streamlit as st
from google import genai
from google.genai import types

# Setup logging to both console and file
LOG_FILENAME = "ai_voice_assistant.log"
logging.basicConfig(
    
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
     handlers=[
    #     logging.FileHandler(LOG_FILENAME),  # Save logs to file
    #     logging.StreamHandler(sys.stdout)   # Print logs to console
     logging.StreamHandler(sys.stdout)   # Print logs only to console
    ]
)

if sys.version_info < (3, 11, 0):
    import taskgroup, exceptiongroup
    asyncio.TaskGroup = taskgroup.TaskGroup
    asyncio.ExceptionGroup = exceptiongroup.ExceptionGroup

# Constants for audio streaming
FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 26000
CHUNK_SIZE = 1024
MODEL = "models/gemini-2.0-flash-exp"


# AI Configuration with Document Explanation Prompt
CONFIG = {
    
    "system_instruction": types.Content(
        parts=[
            types.Part(
                text="""                                
initial_message =   " नमस्ते! क्रेडमिंट टेक्नोलॉजीज़ मेंआपकास्वागत है।"


await self.session.send(input=initial_message, end_of_turn=True)

क्रेडमिंट एक एम्बेडेड सप्लाई चेन फाइनेंस संगठन है, जो वितरकों, खुदरा विक्रेताओं, आपूर्तिकर्ताओं और सूक्ष्म, लघु एवं मध्यम उद्यमों (SMEs) को वेब और मोबाइल ऐप इंटरफ़ेस के माध्यम से कार्यशील पूंजी (Working Capital) समाधान प्रदान करता है।

हमारा मुख्य उद्देश्य है कि आपूर्ति श्रृंखलाओं (Supply Chains) में तेज़ ऋण पहुँच (Faster Credit Access), बेहतर नकदी प्रवाह (Better Cash Flow) और व्यवसायिक वृद्धि (Business Growth) को समर्थन मिल सके।
Kredmint offer karta hai:

Distribution / Retailer Finance

Invoice Discounting (ID)

Pre-Invoice Discounting (PID)

Supplier Invoice Discounting (SID)

Term Loans

Customers Kredmint App ya Web Portal use karke yeh kar sakte hain:

Loan aur financing products ke liye apply karna

Documents upload karna

Loan status track karna

Repayment schedules dekhna

Apni incomplete applications continue karna

2. Product Details
A. Distribution / Retailer Finance

Description:
Distributors aur retailers ko credit provide kiya jata hai taaki wo brands se stock purchase kar saken aur apna inventory smoothly manage kar saken.

Eligibility:

Registered distributor ya retailer with brand tie-ups

Business vintage: minimum 1 year

Minimum turnover as per lender policy

Required Documents:

Business PAN

GST Certificate (agar applicable ho)

Last 6 months bank statement

KYC of proprietor/partners/directors (PAN, Aadhaar)

Brand/distributor agreement (agar required ho)

Common Queries:

Q: Loan limit kitni hoti hai?
A: Turnover, repayment history aur lender ke assessment ke basis pe decide hota hai.

Q: Repayment kaise karna hoga?
A: Kredmint App ke through auto-debit, UPI ya net banking se.

B. Invoice Discounting (ID)

Description:
Businesses apne raised invoices ko discount karke early payment le sakte hain Kredmint ke partner lenders se.

Eligibility:

Registered business entity

Valid GST registration (agar applicable ho)

Invoices reputed buyers/anchors ko raise honi chahiye

Required Documents:

Invoice copy

Business PAN

GST certificate

Last 6 months bank statement

Business owner ka KYC

Common Queries:

Q: Invoice submit karne ke baad kitne time me funds milte hain?
A: Normally 24–72 hours ke andar verification ke baad.

Q: Kya multiple invoices discount ho sakte hain?
A: Haan, sanctioned limit ke hisaab se.

C. Pre-Invoice Discounting (PID)

Description:
Invoice raise karne se pehle hi working capital provide hota hai, mostly anchor/brand ke purchase orders ke basis par.

Eligibility:

Vendor/supplier jinke paas confirmed purchase orders ho

Anchor/brand approval required ho sakta hai

Required Documents:

Purchase order copy

KYC aur GST documents

Bank statements

Common Queries:

Q: PID aur Invoice Discounting me difference kya hai?
A: PID me funds invoice generate hone se pehle milte hain (based on PO), jabki ID me raised invoice ke against milte hain.

D. Supplier Invoice Discounting (SID)

Description:
Suppliers apne invoices ko discount karke distributors/anchors se early payment le sakte hain.

Eligibility & Documents:

Invoice Discounting ke jaise hi

Invoices approved anchors ko raise hone chahiye

Common Queries:

Q: Agar buyer payment delay kare to kya hoga?
A: Kredmint lenders ke sath milke recovery karta hai; customer ki obligation loan terms pe depend karegi.

E. Term Loans

Description:
Short-to-mid term loans diye jaate hain business expansion, inventory purchase ya working capital needs ke liye.

Eligibility:

Registered business

Preferably 2+ years operations

Positive financial history

Required Documents:

Business PAN & GST

Last 12 months bank statements

Financial statements (P&L, Balance Sheet)

Business owners ka KYC

Loan Amount: ₹50,000 ✅ Tenure: 12 months ✅ Interest Rate: 20% ✅ Processing Fees (incl. GST): 2.5% [₹1,250 + ₹225 GST] ✅ Monthly EMI: ₹4,632 ✅ Total Interest Payable: ₹4,632 x 12 months - ₹50,000 (Principal) = ₹5,584 ✅ Annual Percentage Rate (APR): 25.85% ✅ Disbursed Amount: ₹50,000 - ₹1,475 = ₹48,525 ✅ Total Amount Payable: ₹4,632 x 12 months = ₹55,584 ✅ Total Cost of the Loan: Interest Amount + Processing Fees = ₹5,584 + ₹1,250 = ₹6,834

Common Queries:

Q: Repayment tenure kitna hota hai?
A: 6–36 months, loan structure ke basis pe.

Q: Kya prepayment allowed hai?
A: Haan, lekin lender ke prepayment terms ke according.

3. Onboarding Process

Kredmint App download karo ya Web Portal visit karo.

Business details aur mobile number se register karo.

KYC, GST aur financial documents upload karo.

Product choose karo (Distribution Finance, ID, SID, PID, Term Loan).

Application Kredmint & lending partner review karenge.

Approval/rejection ka notification app & SMS ke through milega.

Agar approved ho jaye to loan directly bank account me disburse hoga.

4. Customer Support Guidelines

Hamesha customer ko politely greet karo.

Query answer karne se pehle product type confirm karo.

Customer ko guide karo ki Kredmint App login karke loan status, repayment schedules ya pending applications check karein.

Agar customer documents ke baare me pooche → product-specific requirements batao.

Repayment issue ho → app > Repayment section me direct karo.

Technical issue ho → customer ko bolo care@kredmint.com
 par mail bhejein.Conclusion:
Customer support ka number → Customer Care: +91-9818399611

✅ Why Choose Kredmint?

10,000+ MSMEs ka trust, 100+ cities me presence

Fast online application & approval process

Transparent terms, koi hidden charges nahi

Secure aur RBI-compliant processes

24x7 customer support available

Repayment period: 90 din se 365 din tak

Annual Percentage Rate (APR): 10% se 36% tak


""")
    
    
        ]
),

    "response_modalities": ["AUDIO"],
    
}


GEMINI_API_KEY = "AIzaSyAl8ujXhFztHalMAhjPfOWw5zaGqn_Byww"  # Replace with your actual API key
client = genai.Client(api_key=GEMINI_API_KEY, http_options={'api_version': 'v1alpha'})
pya = pyaudio.PyAudio()

# class AudioLoop:
#     def _init_(self):
#         self.audio_in_queue = None
#         self.out_queue = None
#         self.session = None
#         self.running = True  # ✅ Running state flag

#     async def listen_audio(self):
#         try:
#             mic_info = pya.get_default_input_device_info()
#             self.audio_stream = await asyncio.to_thread(
#                 pya.open,
#                 format=FORMAT,
#                 channels=CHANNELS,
#                 rate=SEND_SAMPLE_RATE,
#                 input=True,
#                 input_device_index=mic_info["index"],
#                 frames_per_buffer=CHUNK_SIZE,
#             )
#             while self.running:   # ✅ Check running state
#                 data = await asyncio.to_thread(self.audio_stream.read, CHUNK_SIZE, exception_on_overflow=False)
#                 await self.out_queue.put({"data": data, "mime_type": "audio/pcm"})
#         except Exception as e:
#             logging.error(f"❌ Error in listen_audio: {e}")

#     async def run(self):
#         try:
#             async with (
#                 client.aio.live.connect(model=MODEL, config=CONFIG) as session,
#                 asyncio.TaskGroup() as tg,
#             ):
#                 self.session = session
#                 self.audio_in_queue = asyncio.Queue()
#                 self.out_queue = asyncio.Queue(maxsize=5)

#                 # Initial message
#                 await self.session.send(input="Start explaining document...", end_of_turn=True)

#                 # Start tasks
#                 tg.create_task(self.listen_audio())
#                 tg.create_task(self.send_audio())
#                 tg.create_task(self.receive_audio())
#                 tg.create_task(self.play_audio())

#         except asyncio.CancelledError:
#             logging.warning("Tasks cancelled. Shutting down.")
#         except Exception as e:
#             logging.error(f"❌ Exception in run: {e}")

#     def stop(self):   # ✅ New method
#         logging.info("🛑 Stopping AudioLoop...")
#         self.running = False
        

#     async def listen_audio(self):
#         """Captures microphone audio and sends it to AI in real-time."""
#         try:
#             logging.info("🔊 Initializing microphone for listening...")
#             mic_info = pya.get_default_input_device_info()
#             self.audio_stream = await asyncio.to_thread(
#                 pya.open,
#                 format=FORMAT,
#                 channels=CHANNELS,
#                 rate=SEND_SAMPLE_RATE,
#                 input=True,
#                 input_device_index=mic_info["index"],
#                 frames_per_buffer=CHUNK_SIZE,
#             )
#             logging.info("🎤 Microphone initialized successfully.")

#             while True:
#                 data = await asyncio.to_thread(self.audio_stream.read, CHUNK_SIZE, exception_on_overflow=False)
#                 logging.debug("🎙️ Captured audio chunk from microphone.")
#                 await self.out_queue.put({"data": data, "mime_type": "audio/pcm"})
        
#         except Exception as e:
#             logging.error(f"❌ Error in listen_audio: {e}")
#             traceback.print_exc()

#     async def send_audio(self):
#         """Sends recorded audio chunks to AI."""
#         try:
#             while True:
#                 msg = await self.out_queue.get()
#                 logging.debug("📤 Sending audio chunk to AI...")
#                 await self.session.send(input=msg)
#         except Exception as e:
#             logging.error(f"❌ Error in send_audio: {e}")
#             traceback.print_exc()

#     async def receive_audio(self):
#         """Receives AI-generated audio responses and places them in the queue."""
#         try:
#             while True:
#                 turn = self.session.receive()
#                 async for response in turn:
#                     if data := response.data:
#                         logging.debug("🔊 Received AI audio response.")
#                         self.audio_in_queue.put_nowait(data)
#                     if text := response.text:
#                         logging.info(f"🤖 AI: {text}")

#                 while not self.audio_in_queue.empty():
#                     self.audio_in_queue.get_nowait()
#                     logging.warning("⚠️ User interrupted AI response. Clearing queue.")

#         except Exception as e:
#             logging.error(f"❌ Error in receive_audio: {e}")
#             traceback.print_exc()

#     async def play_audio(self):
#         """Plays AI-generated audio responses in real-time."""
#         try:
#             stream = await asyncio.to_thread(
#                 pya.open,
#                 format=FORMAT,
#                 channels=CHANNELS,
#                 rate=RECEIVE_SAMPLE_RATE,
#                 output=True,
#             )
#             logging.info("🔊 AI audio playback initialized.")
            
#             while True:
#                 bytestream = await self.audio_in_queue.get()
#                 logging.debug("▶️ Playing AI response audio...")
#                 await asyncio.to_thread(stream.write, bytestream)

#         except Exception as e:
#             logging.error(f"❌ Error in play_audio: {e}")
#             traceback.print_exc()

#     async def run(self):
#          """Main function to handle the live AI conversation."""
#          try:
#              logging.info("Connecting to AI model...")

#              async with (
#                  client.aio.live.connect(model=MODEL, config=CONFIG) as session,
#                  asyncio.TaskGroup() as tg,
#              ):
#                  self.session = session
#                  self.audio_in_queue = asyncio.Queue()
#                  self.out_queue = asyncio.Queue(maxsize=5)

#                  logging.info(" AI session established. Starting conversation...")

#                  # ✅ Send an initial message to AI so it starts talking first
#                  initial_message = "Start explaining the document in a structured way."
#                  await self.session.send(input=initial_message, end_of_turn=True)

#                  # ✅ Start the audio tasks
#                  tg.create_task(self.listen_audio())
#                  tg.create_task(self.send_audio())
#                  tg.create_task(self.receive_audio())
#                  tg.create_task(self.play_audio())

#          except asyncio.CancelledError:
#              logging.warning("Async tasks cancelled. Shutting down.")
#          except ExceptionGroup as EG:
#              self.audio_stream.close()
#              logging.error(" ExceptionGroup encountered in run().")
#              traceback.print_exception(EG)

class AudioLoop:
    def __init__(self):
        self.audio_in_queue = None
        self.out_queue = None
        self.session = None
        self.running = True   # ✅ initialize properly
        self.audio_stream = None

    def stop(self):   # ✅ This now works
        logging.info("🛑 Stopping AudioLoop...")
        self.running = False
        if self.audio_stream:
            self.audio_stream.close()

    async def listen_audio(self):
        """Captures microphone audio and sends it to AI in real-time."""
        try:
            logging.info("🔊 Initializing microphone for listening...")
            mic_info = pya.get_default_input_device_info()
            self.audio_stream = await asyncio.to_thread(
                pya.open,
                format=FORMAT,
                channels=CHANNELS,
                rate=SEND_SAMPLE_RATE,
                input=True,
                input_device_index=mic_info["index"],
                frames_per_buffer=CHUNK_SIZE,
            )
            logging.info("🎤 Microphone initialized successfully.")

            while self.running:   # ✅ check running flag
                data = await asyncio.to_thread(
                    self.audio_stream.read, CHUNK_SIZE, exception_on_overflow=False
                )
                await self.out_queue.put({"data": data, "mime_type": "audio/pcm"})
        
        except Exception as e:
            logging.error(f"❌ Error in listen_audio: {e}")
            traceback.print_exc()

    async def send_audio(self):
        try:
            while self.running:   # ✅ check running flag
                msg = await self.out_queue.get()
                await self.session.send(input=msg)
        except Exception as e:
            logging.error(f"❌ Error in send_audio: {e}")
            traceback.print_exc()

    async def receive_audio(self):
        try:
            while self.running:   # ✅ check running flag
                turn = self.session.receive()
                async for response in turn:
                    if data := response.data:
                        self.audio_in_queue.put_nowait(data)
                    if text := response.text:
                        logging.info(f"🤖 AI: {text}")

        except Exception as e:
            logging.error(f"❌ Error in receive_audio: {e}")
            traceback.print_exc()

    async def play_audio(self):
        try:
            stream = await asyncio.to_thread(
                pya.open,
                format=FORMAT,
                channels=CHANNELS,
                rate=RECEIVE_SAMPLE_RATE,
                output=True,
            )
            logging.info("🔊 AI audio playback initialized.")
            
            while self.running:   # ✅ check running flag
                bytestream = await self.audio_in_queue.get()
                await asyncio.to_thread(stream.write, bytestream)

        except Exception as e:
            logging.error(f"❌ Error in play_audio: {e}")
            traceback.print_exc()

    async def run(self):
        """Main function to handle the live AI conversation."""
        try:
            logging.info("Connecting to AI model...")

            async with (
                client.aio.live.connect(model=MODEL, config=CONFIG) as session,
                asyncio.TaskGroup() as tg,
            ):
                self.session = session
                self.audio_in_queue = asyncio.Queue()
                self.out_queue = asyncio.Queue(maxsize=5)

                logging.info("✅ AI session established. Starting conversation...")

                await self.session.send(
                    input="Start explaining the document in a structured way.",
                    end_of_turn=True,
                )

                tg.create_task(self.listen_audio())
                tg.create_task(self.send_audio())
                tg.create_task(self.receive_audio())
                tg.create_task(self.play_audio())

        except asyncio.CancelledError:
            logging.warning("Async tasks cancelled. Shutting down.")
        except Exception as e:
            logging.error(f"❌ Exception in run: {e}")
            traceback.print_exc()


# Streamlit UI
def streamlit_ui():
    st.set_page_config(page_title="AI Voice Assistant", layout="centered")
     # 🎨 CSS for glowing circle + call icon button
    st.markdown("""
        <style>
        .glow {
            width: 120px;
            height: 120px;
            background-color: #34eb6b;
            border-radius: 50%;
            box-shadow: 0 0 20px #34eb6b, 0 0 40px #34eb6b, 0 0 60px #34eb6b;
            margin: auto;
            animation: pulse 1.5s infinite;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        @keyframes pulse {
            0% { box-shadow: 0 0 10px #34eb6b, 0 0 20px #34eb6b; }
            50% { box-shadow: 0 0 40px #34eb6b, 0 0 80px #34eb6b; }
            100% { box-shadow: 0 0 10px #34eb6b, 0 0 20px #34eb6b; }
        }
        .call-button {
            width: 80px;
            height: 80px;
            background-color: #25D366; /* WhatsApp green */
            border-radius: 50%;
            border: none;
            color: white;
            font-size: 40px;
            cursor: pointer;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("Kredsupport assistant🎙")


    st.write("Hello! Welcome to Kredmint.We’re a leading fintech platform committed to empowering MSMEs and individuals with instant, collateral-free loans,Supply Chain Finance and digital credit solutions. Our expert team helps you understand your options, choose the right plan, and guides you throughout — from application to repayment.With RBI-registered partners, competitive interest rates, and digital-first processes, Kredmint makes credit access simple, secure, and supportive — like a trusted financial partner by your side. At Kredmint, we’re always with you — like a family.")
    
    # Store AudioLoop object in Streamlit session_state so it persists
    if "audio_loop" not in st.session_state:
        st.session_state.audio_loop = None

    # Start Button
    if st.button("📞"):
        if st.session_state.audio_loop is None:
            logging.info("🚀 AI Call Started...")
            st.session_state.audio_loop = AudioLoop()
            asyncio.run(st.session_state.audio_loop.run())
        else:
            st.warning("Assistant already running!")

    # Stop Button
    if st.button("🛑 Stop"):
        if st.session_state.audio_loop is not None:
            logging.info("🛑 Stopping AI Assistant...")
            st.session_state.audio_loop.stop()
            st.session_state.audio_loop = None
            st.success("Assistant stopped successfully.")
        else:
            st.warning("Assistant is not running.")

    # # 🚀 Streamlit doesn’t catch raw HTML clicks directly
    # # Workaround: use an actual st.button next to it
    # if st.button("📞", key="real_call_button"):
    #     logging.info(" AI Call Started...")
    #     main = AudioLoop()
    #     asyncio.run(main.run())
        # st.success("AI Voice Assistant started")

if __name__ == "__main__":
    streamlit_ui()