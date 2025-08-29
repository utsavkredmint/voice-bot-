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
CHUNK_SIZE = 512
MODEL = "models/gemini-2.0-flash-exp"


# AI Configuration with Document Explanation Prompt
CONFIG = {
    
    "system_instruction": types.Content(
        parts=[
            types.Part(
                text="""

                                
initial_message = "नमस्ते! क्रेडमिंट टेक्नोलॉजीज़ में आपका स्वागत है।"


await self.session.send(input=initial_message, end_of_turn=True)

Kredmint आपका ऑल-इन-वन वित्तीय पार्टनर है, जो माइक्रो, स्मॉल और मीडियम एंटरप्राइजेज (MSMEs) को तेज़, सुरक्षित और भरोसेमंद वित्तीय सेवाओं तक पहुँचने में मदद करता है। चाहे आपको वर्किंग कैपिटल की ज़रूरत हो, फ्लेक्सिबल पेमेंट सॉल्यूशंस चाहिए, या प्रभावी खर्च प्रबंधन — Kredmint आपकी वित्तीय यात्रा को सरल बनाता है।

Key Features

✅ Business Loans: ₹50 लाख तक का तत्काल, बिना गारंटी वाला बिज़नेस लोन प्राप्त करें। Kredmint अपने RBI-registered NBFC और प्रमुख वित्तीय संस्थानों के साथ साझेदारी करता है ताकि सुरक्षित और कंप्लायंट लेंडिंग सुनिश्चित की जा सके, जल्दी अप्रूवल और न्यूनतम कागजी कार्रवाई के साथ।

✅ Business Cards: Kredmint के स्मार्ट बिज़नेस कार्ड के साथ अपने व्यापारिक खर्चों पर नियंत्रण रखें। खर्च ट्रैक करें, कर्मचारी खर्चों का प्रबंधन करें और अपनी वित्तीय प्रक्रियाओं को रियल-टाइम में सरल बनाएं।

✅ Bill Payments: यूटिलिटी, वेंडर, सप्लायर आदि के बिल आसानी से ऐप के माध्यम से भुगतान करें और समय बचाएँ।

Our Customers

10,000+ MSMEs, 100+ शहरों में, जिन्होंने पहले ही Kredmint के माध्यम से फंडिंग सुरक्षित की और अपने वित्त को सरल बनाया।

What We Offer

इनवॉइस डिस्काउंटिंग

सप्लाई चेन फाइनेंस

लाइन ऑफ़ क्रेडिट

टर्म लोन

मर्चेंट कैश एडवांस

लेटर ऑफ़ क्रेडिट

लोन अगेंस्ट प्रॉपर्टी

Why Choose Kredmint?

10,000+ MSMEs द्वारा भरोसा

तेज़ ऑनलाइन आवेदन और अप्रूवल

पारदर्शी शर्तें, कोई छिपा शुल्क नहीं

सुरक्षित और RBI-अनुरूप प्रक्रियाएं

24x7 ग्राहक सहायता

पुनर्भुगतान अवधि: 90 दिन से 365 दिन तक

वार्षिक ब्याज दर (APR): 10% से 36% तक

Example of How Kredmint Business Loan Works

Loan Amount: ₹50,000

Tenure: 12 महीने

Interest Rate: 20%

Processing Fees (incl. GST): 2.5% [₹1,250 + ₹225 GST]

Monthly EMI: ₹4,632

Total Interest Payable: ₹4,632 × 12 - ₹50,000 = ₹5,584

Annual Percentage Rate (APR): 25.85%

Disbursed Amount: ₹50,000 - ₹1,475 = ₹48,525

Total Amount Payable: ₹4,632 × 12 = ₹55,584

Total Cost of the Loan: ब्याज + प्रोसेसिंग फीस = ₹5,584 + ₹1,250 = ₹6,834

नोट: ये आंकड़े केवल उदाहरण के लिए हैं। अंतिम ब्याज दर और APR ग्राहक के क्रेडिट मूल्यांकन पर निर्भर करेगी, जैसा कि Kredmint Lending Partner(s) तय करेंगे।

                

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
Invoice Financing	1–3% प्रति माह	Short-term	बकाया चालानों के खिलाफ वित्त पोषण
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

9. Collections (भुगतान वसूली)  

Kredmint डिजिटल-first collection solutions देता है ताकि व्यवसाय अपने भुगतानों की वसूली आसानी और सुरक्षा से कर सकें।  

Features:  
- SMS, Email और WhatsApp reminders  
- आसान repayment के लिए Secure Payment Links  
- Repayment Modes: UPI, Net Banking, Debit/Credit Card, Wallets  
- Outstanding dues और settlements का Real-time Dashboard  
- NACH / e-Mandate से Recurring Payments  

Benefits:  
- तेज़ Recovery और कम Operational Cost  
- Flexible Payment Methods से बेहतर Customer Experience  
- Real-time Reporting से बेहतर Cashflow Management 

आप एक सख्त एआई सहायक हैं। हमेशा संक्षिप्त उत्तर दें, 30 शब्दों या उससे कम में। लंबी व्याख्या या अनावश्यक विवरण न दें। केवल उपयोगकर्ता के प्रश्न से संबंधित सबसे महत्वपूर्ण जानकारी पर ध्यान दें।
Conclusion:

"नमस्ते! क्रेडमिंट टेक्नोलॉजीज़ में आपका स्वागत है।"

Kredmint Technologies MSMEs के लिए एक प्रमुख वित्तीय सेवाओं प्रदाता है। नवाचारी उत्पादों और सेवाओं से व्यवसाय और व्यक्तिगत ग्राहकों को वित्तीय प्रबंधन में सहारा मिलता है। Kredmint का उद्देश्य MSMEs और व्यक्तिगत ग्राहकों दोनों को सक्षम बनाना और उन्हें वित्तीय समावेशन की दिशा में मार्गदर्शन करना है।""")
    
    
        ]
),

    "response_modalities": ["AUDIO"],
}

GEMINI_API_KEY = "AIzaSyBxr-OoSVQrIGMTjVfMAcEM00ZaoplPeJQ"  # Replace with your actual API key
client = genai.Client(api_key=GEMINI_API_KEY, http_options={'api_version': 'v1alpha'})
pya = pyaudio.PyAudio()

class AudioLoop:
    def __init__(self):
        self.audio_in_queue = None
        self.out_queue = None
        self.session = None

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
                        self.audio_in_queue.put_nowait(response.data)
                    if text := response.text:
                        logging.info(f"🤖 AI: {response.text}")

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
                #stream.write(bytestream) 
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
    # st.markdown(
    #     """
    #     <style>
    #         .center {
    #             display: flex;
    #             justify-content: center;
    #             align-items: center;
    #             height: 50vh;
    #         }
    #         .glow {
    #             width: 150px;
    #             height: 150px;
    #             background: radial-gradient(circle, rgba(72, 239, 72, 1) 0%, rgba(0, 128, 0, 1) 60%);
    #             border-radius: 50%;
    #             box-shadow: 0px 0px 30px 10px rgba(72, 239, 72, 0.8);
    #             animation: pulse 2s infinite alternate;
    #         }
    #         @keyframes pulse {
    #             0% { box-shadow: 0px 0px 20px 5px rgba(72, 239, 72, 0.6); }
    #             100% { box-shadow: 0px 0px 40px 15px rgba(72, 239, 72, 1); }
    #         }
    #     </style>
    #     <div class="center">
    #         <div class="glow"></div>
    #     </div>
    #     """,
    #     unsafe_allow_html=True
    # )

    # st.title("🎙 AI Voice Assistant")
    # st.write("This assistant listens to your voice and explains the given document in real-time.")

    # if st.button("Start AI Assistant"):
    #     logging.info("🎙 AI Assistant Started...")
    #     main = AudioLoop()
    #     asyncio.run(main.run())

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


    st.write("Hello! Welcome to Kredmint.We’re a leading fintech platform committed to empowering MSMEs and individuals with instant, collateral-free loans, home financing, and digital credit solutions. Our expert team helps you understand your options, choose the right plan, and guides you throughout — from application to repayment.With RBI-registered partners, competitive interest rates, and digital-first processes, Kredmint makes credit access simple, secure, and supportive — like a trusted financial partner by your side. At Kredmint, we’re always with you — like a family.")

    # # 📞 Add call button (using HTML)
    # call_button = st.markdown("""
    #     # <div style="display: flex; justify-content: center; margin-top: 30px;">
    #     #     <button class="call-button" id="startBtn">📞</button>
    #     # </div>
    #     """, unsafe_allow_html=True)

    # 🚀 Streamlit doesn’t catch raw HTML clicks directly
    # Workaround: use an actual st.button next to it
    if st.button("📞", key="real_call_button"):
        logging.info(" AI Call Started...")
        main = AudioLoop()
        asyncio.run(main.run())
        # st.success("AI Voice Assistant started! ")

if __name__ == "__main__":
    streamlit_ui()
