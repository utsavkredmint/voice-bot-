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
        logging.FileHandler(LOG_FILENAME),  # Save logs to file
        logging.StreamHandler(sys.stdout)   # Print logs to console
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

Kredmint आपका ऑल-इन-वन वित्तीय पार्टनर है, जो माइक्रो, स्मॉल और मीडियम एंटरप्राइजेज (MSMEs) को तेज़, सुरक्षित और भरोसेमंद वित्तीय सेवाओं तक पहुँचने में मदद करता है। चाहे आपको वर्किंग कैपिटल की ज़रूरत हो, फ्लेक्सिबल पेमेंट सॉल्यूशंस चाहिए, या प्रभावी खर्च प्रबंधन — Kredmint आपकी वित्तीय यात्रा को सरल बनाता है।

Key Features

✅ Business Loans: ₹50 लाख तक का तत्काल, बिना गारंटी वाला बिज़नेस लोन प्राप्त करें। Kredmint अपने RBI-registered NBFC और प्रमुख वित्तीय संस्थानों के साथ साझेदारी करता है ताकि सुरक्षित और कंप्लायंट लेंडिंग सुनिश्चित की जा सके, जल्दी अप्रूवल और न्यूनतम कागजी कार्रवाई के साथ।

✅ Business Cards: Kredmint के स्मार्ट बिज़नेस कार्ड के साथ अपने व्यापारिक खर्चों पर नियंत्रण रखें। खर्च ट्रैक करें, कर्मचारी खर्चों का प्रबंधन करें और अपनी वित्तीय प्रक्रियाओं को रियल-टाइम में सरल बनाएं।

✅ Bill Payments: यूटिलिटी, वेंडर, सप्लायर आदि के बिल आसानी से ऐप के माध्यम से भुगतान करें और समय बचाएँ।

Our Customers

10,000+ MSMEs, 100+ शहरों में, जिन्होंने पहले ही Kredmint के माध्यम से फंडिंग सुरक्षित की और अपने वित्त को सरल बनाया।

1. Invoice Discounting

Invoice Discounting एक ऐसी सुविधा है जहाँ MSMEs अपनी बकाया invoices (जो clients/vendors ने अभी तक पेमेंट नहीं की) को financial institutions को बेचकर तुरंत पैसे प्राप्त कर सकते हैं।

इससे Cash Flow तुरंत improve होता है।

Working Capital की ज़रूरत बिना इंतज़ार के पूरी हो जाती है।

Business अपनी liquidity बनाए रखता है और growth activities को delay नहीं करता।

2. Supply Chain Finance

यह सुविधा distributors, suppliers और retailers के लिए डिज़ाइन की जाती है।

Suppliers को समय पर पैसा मिल जाता है।

Distributors को flexible repayment period मिलता है।

Business relation मज़बूत होते हैं क्योंकि सभी stakeholders को timely funds मिलते हैं।
👉 इसे Dealer-Distributor Financing भी कहते हैं।

3. Line of Credit

Line of Credit एक revolving credit facility है।

आपको एक limit approve की जाती है (जैसे ₹10 लाख)।

ज़रूरत पड़ने पर उतना पैसा इस्तेमाल कर सकते हैं और repay करने पर limit फिर से free हो जाती है।

Interest केवल उतने amount पर लगता है जितना use किया गया हो।
👉 यह Credit Card की तरह काम करता है लेकिन Business के लिए high-value transactions के साथ।

4. Term Loans

Term Loan एक fixed amount loan होता है जो borrower को एक बार में दिया जाता है और उसे fixed EMI में repay करना होता है।

Tenure: Short Term (1–3 साल) या Long Term (3–10 साल)।

Interest rate fixed या floating हो सकता है।

Best for: Asset Purchase, Machinery, Office Expansion, Infrastructure Investment।

5. Merchant Cash Advance

Merchant Cash Advance एक repayment method है जिसमें MSMEs को future sales के against पैसा मिलता है।

Repayment daily/weekly sales का percentage deduct करके किया जाता है।

Best for: Retailers, Restaurants, E-commerce sellers।

Advantage: EMI pressure नहीं होता क्योंकि repayment sales से linked है।

6. Letter of Credit

Letter of Credit (LC) एक financial guarantee होती है जो बैंक या financial institution exporter को देता है कि उसका पैसा importer से ज़रूर मिलेगा।

International trade में बहुत उपयोगी।

Importer को भरोसा कि goods मिलेंगे।

Exporter को भरोसा कि payment secure है।
👉 यह Trust Building Tool है cross-border trade के लिए।

7. Loan Against Property (LAP)

Loan Against Property एक secured loan है जहाँ borrower अपनी residential/commercial property को गिरवी रखकर loan लेता है।

Loan amount: Property value का 60–70% तक।

Interest rate personal loan से कम होता है।

Long tenure (5–15 साल)।

Best for: Business expansion, Debt consolidation, Higher education, Medical emergency।



Main Products aur Services

1. Business Loans

Kredmint MSMEs को ₹50 लाख तक का त्वरित, बिना गारंटी वाला बिजनेस लोन प्रदान करता है। यह लोन RBI-registered NBFCs और प्रमुख वित्तीय संस्थानों के साथ साझेदारी में उपलब्ध होते हैं।

Customer Loan Process:

Loan Application: ऑनलाइन या ऐप के माध्यम से आवेदन करें।

Documents: आधार, PAN, बैंक स्टेटमेंट और व्यवसाय से संबंधित विवरण अपलोड करना आवश्यक है।

CIBIL Score Check: आमतौर पर CIBIL स्कोर ≥ 650 को अच्छा माना जाता है।

Business Loan Types aur Interest Rates:

आधार कार्ड (Aadhaar Card) – पहचान और पते का प्रमाण

पैन कार्ड (PAN Card) – वित्तीय और टैक्स रिकॉर्ड के लिए आवश्यक

CIBIL Score – आमतौर पर ≥ 650 होना चाहिए (उच्च स्कोर = बेहतर ब्याज दर और तेज़ अप्रूवल)

Income Proof – वेतन पर्चियां, बैंक स्टेटमेंट, या ITR (loan प्रकार के अनुसार)

Business/Employment Proof – बिज़नेस लोन के लिए GST/ROC/बिज़नेस रजिस्ट्रेशन, नौकरीपेशा के लिए salary slips

Property/Asset Documents – होम लोन या कार लोन के लिए संबंधित एसेट के कागजात

Loan Type	Interest Rate	Tenure	Notes
Short-term Working Capital	12–18% p.a.	3–12 महीने	दैनिक व्यावसायिक खर्च; लचीला पुनर्भुगतान
Term Loan	10–16% p.a.	12–36 महीने	लंबी अवधि, EMI पुनर्भुगतान
Invoice Financing   1–3% प्रति माह	Short-term	बकाया चालानों के खिलाफ वित्त पोषण
Vendor Financing	10–15% p.a.	6–24 महीने	सप्लाई चेन भुगतान
Buy Now Pay Later	1–2.5% प्रति माह	1–6 महीने	revolving credit


2. Home Loans

Kredmint अब Home Loans भी प्रदान करता है जिसमें प्रतिस्पर्धी ब्याज दरें और लचीली अवधि विकल्प उपलब्ध हैं।

Home Loan Features:

Loan Amount: ₹5 लाख – ₹3 करोड़

Interest Rate: 8.5% – 12% p.a. (क्रेडिट स्कोर, प्रॉपर्टी लोकेशन और बैंक पॉलिसी पर निर्भर)

Tenure: 5–30 वर्ष

Eligibility: वेतनभोगी, स्व-नियोजित, आयु 21–65 वर्ष

Documents: आधार, PAN, वेतन पर्चियां / व्यवसाय प्रमाण, संपत्ति के कागजात

EMI Calculation Example:

Loan ₹50,00,000 at 9% p.a. for 20 वर्ष (240 महीने)

EMI = ₹44,954 प्रति माह

Taxes & Fees:

प्रोसेसिंग फीस पर GST लागू

यदि होम लोन पर ब्याज की राशि सीमा से अधिक है तो TDS लागू (Income Tax Act)

अन्य शुल्क: प्रोसेसिंग शुल्क 0.25–1% of loan amount, प्रीपेमेंट शुल्क बैंक/NBFC नियमों के अनुसार


4. Interest Rate Overview

ब्याज फिक्स्ड या घटती बैलेंस (reducing balance) हो सकता है।

Short-term loans में थोड़ी अधिक दरें होती हैं; long-term loans में वार्षिक दरें कम होती हैं।

Invoice financing और BNPL आमतौर पर मासिक शुल्क आधारित होते हैं।

Example for Short-term Loan:

Loan ₹10,00,000 at 15% p.a. for 6 महीने

Interest = ₹10,00,000 × 15% × 0.5 = ₹75,000

Total repayment = ₹10,75,000

5. Embedded Financial Solutions

Invoice Discounting, Vendor Financing, White-labeled Solutions

Buy Now, Pay Later, Collection and Payment Solutions

Auto Collect, Easy Split, Escrow Account, Subscription Management

Line of Credit और Trade Finance

6. Technology & Innovation

Scalable order management system

Retailers और distributor network के लिए loyalty programs और discounts

7. Impact & Reach

120+ brands और 300,000+ merchants onboarded

1.2 million+ invoices processed

8. Customer Support

Phone, email, online chat उपलब्ध

तेज़ समाधान और मार्गदर्शन


आप एक सख्त एआई सहायक हैं। हमेशा संक्षिप्त उत्तर दें, 40 शब्दों या उससे कम में। लंबी व्याख्या या अनावश्यक विवरण न दें। केवल उपयोगकर्ता के प्रश्न से संबंधित सबसे महत्वपूर्ण जानकारी पर ध्यान दें।
Conclusion:

Kredmint Technologies MSMEs के लिए एक प्रमुख वित्तीय सेवाओं प्रदाता है। नवाचारी उत्पादों और सेवाओं से व्यवसाय और व्यक्तिगत ग्राहकों को वित्तीय प्रबंधन में सहारा मिलता है। Kredmint का उद्देश्य MSMEs और व्यक्तिगत ग्राहकों दोनों को सक्षम बनाना और उन्हें वित्तीय समावेशन की दिशा में मार्गदर्शन करना है।""")
    
    
        ]
),

    "response_modalities": ["AUDIO"],
    
    
}



GEMINI_API_KEY = "AIzaSyDzGrzwONae3BszBRj70WOSTz5O6zCOnNQ"  # Replace with your actual API key
client = genai.Client(api_key=GEMINI_API_KEY, http_options={'api_version': 'v1alpha'})
pya = pyaudio.PyAudio()

class AudioLoop:
    def _init_(self):
        self.audio_in_queue = None
        self.out_queue = None
        self.session = None
        self.running = True  # ✅ Running state flag

    async def listen_audio(self):
        try:
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
            while self.running:   # ✅ Check running state
                data = await asyncio.to_thread(self.audio_stream.read, CHUNK_SIZE, exception_on_overflow=False)
                await self.out_queue.put({"data": data, "mime_type": "audio/pcm"})
        except Exception as e:
            logging.error(f"❌ Error in listen_audio: {e}")

    async def run(self):
        try:
            async with (
                client.aio.live.connect(model=MODEL, config=CONFIG) as session,
                asyncio.TaskGroup() as tg,
            ):
                self.session = session
                self.audio_in_queue = asyncio.Queue()
                self.out_queue = asyncio.Queue(maxsize=5)

                # Initial message
                await self.session.send(input="Start explaining document...", end_of_turn=True)

                # Start tasks
                tg.create_task(self.listen_audio())
                tg.create_task(self.send_audio())
                tg.create_task(self.receive_audio())
                tg.create_task(self.play_audio())

        except asyncio.CancelledError:
            logging.warning("Tasks cancelled. Shutting down.")
        except Exception as e:
            logging.error(f"❌ Exception in run: {e}")

    def stop(self):   # ✅ New method
        logging.info("🛑 Stopping AudioLoop...")
        self.running = False
        

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

            while True:
                data = await asyncio.to_thread(self.audio_stream.read, CHUNK_SIZE, exception_on_overflow=False)
                logging.debug("🎙️ Captured audio chunk from microphone.")
                await self.out_queue.put({"data": data, "mime_type": "audio/pcm"})
        
        except Exception as e:
            logging.error(f"❌ Error in listen_audio: {e}")
            traceback.print_exc()

    async def send_audio(self):
        """Sends recorded audio chunks to AI."""
        try:
            while True:
                msg = await self.out_queue.get()
                logging.debug("📤 Sending audio chunk to AI...")
                await self.session.send(input=msg)
        except Exception as e:
            logging.error(f"❌ Error in send_audio: {e}")
            traceback.print_exc()

    async def receive_audio(self):
        """Receives AI-generated audio responses and places them in the queue."""
        try:
            while True:
                turn = self.session.receive()
                async for response in turn:
                    if data := response.data:
                        logging.debug("🔊 Received AI audio response.")
                        self.audio_in_queue.put_nowait(data)
                    if text := response.text:
                        logging.info(f"🤖 AI: {text}")

                while not self.audio_in_queue.empty():
                    self.audio_in_queue.get_nowait()
                    logging.warning("⚠️ User interrupted AI response. Clearing queue.")

        except Exception as e:
            logging.error(f"❌ Error in receive_audio: {e}")
            traceback.print_exc()

    async def play_audio(self):
        """Plays AI-generated audio responses in real-time."""
        try:
            stream = await asyncio.to_thread(
                pya.open,
                format=FORMAT,
                channels=CHANNELS,
                rate=RECEIVE_SAMPLE_RATE,
                output=True,
            )
            logging.info("🔊 AI audio playback initialized.")
            
            while True:
                bytestream = await self.audio_in_queue.get()
                logging.debug("▶️ Playing AI response audio...")
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

                 logging.info(" AI session established. Starting conversation...")

                 # ✅ Send an initial message to AI so it starts talking first
                 initial_message = "Start explaining the document in a structured way."
                 await self.session.send(input=initial_message, end_of_turn=True)

                 # ✅ Start the audio tasks
                 tg.create_task(self.listen_audio())
                 tg.create_task(self.send_audio())
                 tg.create_task(self.receive_audio())
                 tg.create_task(self.play_audio())

         except asyncio.CancelledError:
             logging.warning("Async tasks cancelled. Shutting down.")
         except ExceptionGroup as EG:
             self.audio_stream.close()
             logging.error(" ExceptionGroup encountered in run().")
             traceback.print_exception(EG)


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
