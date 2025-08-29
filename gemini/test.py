# ai_voice_assistant.py
# Full rewrite with low-latency streaming for Gemini Live API
# Replace GEMINI_API_KEY with your actual key (or better: load from env vars)

import os
import asyncio
import logging
import traceback
import sys
import pyaudio
import streamlit as st
from google import genai
from google.genai import types

# ----------------- Configuration / Constants -----------------
LOG_FILENAME = "ai_voice_assistant.log"
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILENAME),
        logging.StreamHandler(sys.stdout),
    ],
)

# Compatibility for older Python if necessary (kept safe)
if sys.version_info < (3, 11, 0):
    import taskgroup, exceptiongroup
    asyncio.TaskGroup = taskgroup.TaskGroup
    asyncio.ExceptionGroup = exceptiongroup.ExceptionGroup

# Audio constants (recommended low-latency values)
FORMAT = pyaudio.paInt16
CHANNELS = 1
CHUNK_SIZE = 512              # smaller chunk -> lower latency
SEND_SAMPLE_RATE = 16000      # mic capture sample rate
RECEIVE_SAMPLE_RATE = 24000   # model audio playback sample rate
MODEL = "models/gemini-2.0-flash-exp"

# AI Configuration (short system instruction is OK; keep heavy prompts off the critical path)
CONFIG = {
    "system_instruction": types.Content(
        parts=[
            types.Part(
                text=(
                    "आप एक सहायक हैं जो दस्तावेज़ों को संक्षेप में और स्पष्ट रूप से समझाता है। "
                    "हिंदी में संक्षिप्त, सहायक उत्तर दें।"
                )
            )
        ]
    ),
    "response_modalities": ["AUDIO"],
}

# GEMINI API key — prefer environment variable
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyBxr-OoSVQrIGMTjVfMAcEM00ZaoplPeJQ")
if GEMINI_API_KEY == "AIzaSyBxr-OoSVQrIGMTjVfMAcEM00ZaoplPeJQ":
    logging.warning("GEMINI_API_KEY not set. Replace it or set env var GEMINI_API_KEY.")

client = genai.Client(api_key=GEMINI_API_KEY, http_options={"api_version": "v1alpha"})


# ----------------- Low-latency AudioLoop -----------------
class AudioLoop:
    def __init__(self):
        self.audio_in_queue: asyncio.Queue | None = None
        self.out_queue: asyncio.Queue | None = None
        self.session = None
        self.audio_stream = None
        self.play_stream = None
        self._pya = pyaudio.PyAudio()

    async def listen_audio(self):
        """Read mic and push PCM chunks to out_queue."""
        try:
            logging.info("🔊 Initializing microphone for listening...")
            mic_info = self._pya.get_default_input_device_info()

            # Open microphone stream (threaded via asyncio.to_thread)
            self.audio_stream = await asyncio.to_thread(
                self._pya.open,
                format=FORMAT,
                channels=CHANNELS,
                rate=SEND_SAMPLE_RATE,
                input=True,
                input_device_index=mic_info.get("index"),
                frames_per_buffer=CHUNK_SIZE,
            )
            logging.info("🎤 Microphone ready.")

            while True:
                data = await asyncio.to_thread(self.audio_stream.read, CHUNK_SIZE, False)
                # Put with backpressure: await if queue full
                await self.out_queue.put({"data": data, "mime_type": "audio/pcm"})
                logging.debug(f"🎙️ Captured and queued {len(data)} bytes")
        except Exception as e:
            logging.error(f"❌ Error in listen_audio: {e}")
            traceback.print_exc()

    async def send_audio(self):
        """Pop mic chunks and send to Gemini immediately (end_of_turn=False by default)."""
        try:
            while True:
                msg = await self.out_queue.get()
                # Send without forcing large end_of_turn so model can stream
                await self.session.send(input=msg)
                logging.debug("📤 Sent audio chunk to AI")
        except Exception as e:
            logging.error(f"❌ Error in send_audio: {e}")
            traceback.print_exc()

    async def receive_audio(self):
        """Consume streaming responses from Gemini as they arrive."""
        try:
            async for response in self.session.receive():
                # Audio chunks
                if getattr(response, "data", None):
                    await self.audio_in_queue.put(response.data)
                    logging.debug(f"🔊 Queued AI audio chunk ({len(response.data)} bytes)")
                # Partial text (optional)
                if getattr(response, "text", None):
                    logging.info(f"🤖 AI (partial text): {response.text}")
        except Exception as e:
            logging.error(f"❌ Error in receive_audio: {e}")
            traceback.print_exc()

    async def play_audio(self):
        """Play audio chunks as soon as they arrive."""
        try:
            self.play_stream = await asyncio.to_thread(
                self._pya.open,
                format=FORMAT,
                channels=CHANNELS,
                rate=RECEIVE_SAMPLE_RATE,
                output=True,
            )
            logging.info("🔊 Playback stream ready.")

            while True:
                chunk = await self.audio_in_queue.get()
                # Play immediately in a thread to avoid blocking event loop
                await asyncio.to_thread(self.play_stream.write, chunk)
                logging.debug(f"▶️ Played {len(chunk)} bytes")
        except Exception as e:
            logging.error(f"❌ Error in play_audio: {e}")
            traceback.print_exc()
        finally:
            try:
                if self.play_stream:
                    self.play_stream.stop_stream()
                    self.play_stream.close()
            except Exception:
                pass

    async def run(self, initial_message: str = "नमस्ते, शुरू करें।"):
        """Create live session, start tasks, and keep them running.

        Use a short initial message so the model emits audio quickly.
        """
        try:
            logging.info("Connecting to AI model...")

            async with (
                client.aio.live.connect(model=MODEL, config=CONFIG) as session,
                asyncio.TaskGroup() as tg,
            ):
                self.session = session
                # Queues sized to provide smooth playback but bound to avoid memory growth
                self.audio_in_queue = asyncio.Queue(maxsize=64)
                self.out_queue = asyncio.Queue(maxsize=32)

                logging.info("✅ AI session established")

                # Send a short initial prompt to begin TTS quickly
                await self.session.send(input=initial_message, end_of_turn=True)

                tg.create_task(self.listen_audio())
                tg.create_task(self.send_audio())
                tg.create_task(self.receive_audio())
                tg.create_task(self.play_audio())

        except asyncio.CancelledError:
            logging.warning("Async tasks cancelled")
        except Exception as e:
            logging.error(f"❌ Exception in run(): {e}")
            traceback.print_exc()
        finally:
            # cleanup mic resources
            try:
                if self.audio_stream:
                    self.audio_stream.stop_stream()
                    self.audio_stream.close()
            except Exception:
                pass


# ----------------- Streamlit UI -----------------
def streamlit_ui():
    st.set_page_config(page_title="AI Voice Assistant", layout="centered")

    st.title("Kredsupport Assistant 🎙️")
    st.write("Click the call button to start a live voice session with the AI.")

    initial_text = st.text_input("Initial prompt (short):", "नमस्ते, शुरू करें।")

    if st.button("📞 Start Call"):
        logging.info("User triggered AI call")
        main = AudioLoop()
        # Run the audio loop synchronously from Streamlit button handler
        try:
            asyncio.run(main.run(initial_message=initial_text))
        except Exception as e:
            logging.error(f"Failed to start AudioLoop: {e}")
            st.error(f"Error: {e}")

    st.caption("Recommended: CHUNK_SIZE=512, SEND_SAMPLE_RATE=16000, RECEIVE_SAMPLE_RATE=24000")


if __name__ == "__main__":
    streamlit_ui()
