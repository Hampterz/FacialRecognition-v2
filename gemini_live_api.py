# gemini_live_api.py - Gemini Live API Integration using Official SDK

import asyncio
import threading
import queue
from typing import Optional, Callable
import time
import sys

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    genai = None
    types = None

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    pyaudio = None


class GeminiLiveAPI:
    """Client-to-server Gemini Live API integration using Official Google GenAI SDK."""
    
    # Audio format constants
    INPUT_SAMPLE_RATE = 16000  # 16kHz input
    OUTPUT_SAMPLE_RATE = 24000  # 24kHz output
    CHANNELS = 1  # Mono
    CHUNK_SIZE = 1024  # Audio chunk size
    FORMAT = pyaudio.paInt16 if PYAUDIO_AVAILABLE else None
    BYTES_PER_SAMPLE = 2  # 16-bit = 2 bytes
    
    def __init__(self, api_key: str):
        """
        Initialize Gemini Live API client.
        
        Args:
            api_key: Google Gemini API key
        """
        if not GENAI_AVAILABLE:
            raise ImportError(
                "google-genai package is required. Install it with: pip install google-genai"
            )
        
        if not PYAUDIO_AVAILABLE:
            raise ImportError(
                "PyAudio is required. Install it with: pip install pyaudio"
            )
        
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key)
        self.session = None
        self.audio_input_stream = None
        self.audio_output_stream = None
        self.pyaudio_instance = None
        self.is_connected = False
        self.is_streaming = False
        
        # Queues for message handling
        self.message_queue = queue.Queue()
        self.audio_output_queue = asyncio.Queue(maxsize=100)  # Larger queue to prevent blocking
        self.audio_input_queue = asyncio.Queue(maxsize=5)
        
        # Callbacks
        self.on_message_callback: Optional[Callable] = None
        self.on_error_callback: Optional[Callable] = None
        self.on_connect_callback: Optional[Callable] = None
        self.on_disconnect_callback: Optional[Callable] = None
        
        # Thread management
        self.async_thread: Optional[threading.Thread] = None
        self.audio_input_thread: Optional[threading.Thread] = None
        self.audio_output_thread: Optional[threading.Thread] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        
        # Model configuration - use native audio model for Live API
        self.model = "gemini-2.5-flash-native-audio-preview-12-2025"
        
        # Configuration - match official example format
        # Audio format is handled by PyAudio streams, not in config
        self.config = {
            "response_modalities": ["AUDIO"],
            "system_instruction": "You are a helpful and friendly AI assistant. Respond naturally in conversation. Keep responses concise and conversational."
        }
    
    def set_callbacks(
        self,
        on_message: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
        on_connect: Optional[Callable] = None,
        on_disconnect: Optional[Callable] = None
    ):
        """Set callback functions for events."""
        self.on_message_callback = on_message
        self.on_error_callback = on_error
        self.on_connect_callback = on_connect
        self.on_disconnect_callback = on_disconnect
    
    async def _run_live_session(self):
        """Run the main Live API session."""
        try:
            print(f"🔗 Connecting to Gemini Live API...")
            print(f"   Model: {self.model}")
            print(f"   API Key length: {len(self.api_key)} characters")
            
            async with self.client.aio.live.connect(
                model=self.model,
                config=self.config
            ) as session:
                self.session = session
                self.is_connected = True
                print("✓ Connected to Gemini Live API")
                
                if self.on_connect_callback:
                    self.on_connect_callback()
                
                # Enable streaming automatically when connected
                if not self.is_streaming:
                    print("🎤 Enabling audio streaming automatically...")
                    self.is_streaming = True
                
                # Wait a moment for connection to stabilize
                await asyncio.sleep(0.5)
                
                print("🎤 Ready to start conversation!")
                
                # Start all async tasks - all should run simultaneously
                async with asyncio.TaskGroup() as tg:
                    # Always start receiving (to get responses)
                    tg.create_task(self._receive_audio(session))
                    
                    # Start audio tasks (streaming is now enabled)
                    tg.create_task(self._send_realtime_audio(session))
                    tg.create_task(self._listen_audio())
                    tg.create_task(self._play_audio())
                    
        except Exception as e:
            self.is_connected = False
            print(f"❌ Live API Error: {e}")
            if self.on_error_callback:
                self.on_error_callback(e)
        finally:
            self.is_connected = False
            self.is_streaming = False
            if self.on_disconnect_callback:
                self.on_disconnect_callback()
            print("✗ Disconnected from Gemini Live API")
    
    async def _listen_audio(self):
        """Listens for audio from microphone and puts it into the input queue.
        
        Based on official example: https://ai.google.dev/gemini-api/docs/live?example=mic-stream
        Input format: 16-bit PCM, 16kHz, mono (LINEAR16)
        """
        if not self.pyaudio_instance:
            self.pyaudio_instance = pyaudio.PyAudio()
        
        try:
            mic_info = self.pyaudio_instance.get_default_input_device_info()
            print(f"🎤 Using microphone: {mic_info.get('name', 'Default')}")
        except Exception as e:
            print(f"⚠️ Could not get mic info: {e}, using default")
            mic_info = {"index": None}
        
        # Open microphone stream with correct format (16-bit PCM, 16kHz, mono)
        self.audio_input_stream = await asyncio.to_thread(
            self.pyaudio_instance.open,
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.INPUT_SAMPLE_RATE,
            input=True,
            input_device_index=mic_info.get("index") if mic_info.get("index") is not None else None,
            frames_per_buffer=self.CHUNK_SIZE,
        )
        
        print("🎤 Microphone stream started - speak now!")
        print(f"   Format: {self.FORMAT} (16-bit PCM)")
        print(f"   Sample Rate: {self.INPUT_SAMPLE_RATE} Hz")
        print(f"   Channels: {self.CHANNELS} (mono)")
        print(f"   Chunk Size: {self.CHUNK_SIZE} frames")
        
        # Use exception_on_overflow=False in debug mode (matches official example)
        kwargs = {"exception_on_overflow": False} if __debug__ else {}
        chunk_count = 0
        
        while self.is_streaming and self.is_connected:
            try:
                # Read audio data from microphone
                data = await asyncio.to_thread(
                    self.audio_input_stream.read,
                    self.CHUNK_SIZE,
                    **kwargs
                )
                
                # Verify data format (should be bytes, 16-bit = 2 bytes per sample)
                if not isinstance(data, bytes):
                    print(f"⚠️ Warning: Audio data is not bytes, got {type(data)}")
                    continue
                
                # Put audio in queue for sending - format matches official example
                await self.audio_input_queue.put({
                    "data": data,
                    "mime_type": "audio/pcm"
                })
                
                chunk_count += 1
                if chunk_count == 1:
                    print("🎤 Capturing audio from microphone...")
                    
            except asyncio.CancelledError:
                print("🎤 Audio listener cancelled")
                break
            except Exception as e:
                if self.is_streaming:  # Only log if we're supposed to be streaming
                    print(f"⚠️ Error reading audio: {e}")
                    import traceback
                    traceback.print_exc()
                break
    
    async def _send_realtime_audio(self, session):
        """Sends audio from the input queue to the Live API session."""
        print("📤 Starting audio input sender...")
        chunk_count = 0
        while self.is_streaming and self.is_connected:
            try:
                # Get audio from queue (this will block until audio is available)
                msg = await self.audio_input_queue.get()
                
                # Send to Gemini Live API
                await session.send_realtime_input(audio=msg)
                
                chunk_count += 1
                if chunk_count % 50 == 0:  # Log every 50 chunks to reduce spam
                    print(f"📤 Sent {chunk_count} audio chunks to Gemini...")
                    
            except asyncio.CancelledError:
                print("📤 Audio sender cancelled")
                break
            except Exception as e:
                if self.is_streaming:
                    print(f"⚠️ Error sending audio: {e}")
                    import traceback
                    traceback.print_exc()
                break
    
    async def _receive_audio(self, session):
        """Receives responses from Live API and puts audio/text into queues.
        
        Based on official example: https://ai.google.dev/gemini-api/docs/live?example=mic-stream
        """
        try:
            print("👂 Starting to receive responses from Gemini...")
            # Follow official example pattern exactly
            while True:
                turn = session.receive()
                async for response in turn:
                    # Handle interruptions FIRST - clear queue to stop playback (prevents glitchy replay)
                    if response.server_content and response.server_content.interrupted:
                        print("⚠️ Response interrupted - clearing audio queue")
                        while not self.audio_output_queue.empty():
                            try:
                                self.audio_output_queue.get_nowait()
                            except asyncio.QueueEmpty:
                                break
                        continue  # Skip processing this response
                    
                    # Handle server content (model responses) - check model_turn first
                    if (response.server_content and response.server_content.model_turn):
                        model_turn = response.server_content.model_turn
                        if model_turn.parts:
                            for part in model_turn.parts:
                                # Handle audio data (inline_data) - use put_nowait like official example
                                # Only process inline_data, not response.data (to avoid duplicates)
                                if part.inline_data and isinstance(part.inline_data.data, bytes):
                                    audio_data = part.inline_data.data
                                    # Only add non-empty audio data
                                    if len(audio_data) > 0:
                                        try:
                                            # Use await put() instead of put_nowait for better flow control
                                            await self.audio_output_queue.put(audio_data)
                                            # Only log occasionally to reduce spam
                                            if not hasattr(self, '_audio_received_count'):
                                                self._audio_received_count = 0
                                            self._audio_received_count += 1
                                            if self._audio_received_count % 50 == 0:
                                                print(f"🔊 Received {self._audio_received_count} audio chunks...")
                                        except Exception as queue_error:
                                            print(f"⚠️ Error adding audio to queue: {queue_error}")
                                
                                # Handle text responses
                                if part.text:
                                    text = part.text
                                    print(f"💬 Gemini Text Response: {text}")
                                    if self.on_message_callback:
                                        self.on_message_callback({
                                            "text": text,
                                            "type": "text_response"
                                        })
                    
                    # Handle generation complete
                    if response.server_content and response.server_content.generation_complete:
                        print("✓ Generation complete")
                    
                    # NOTE: We don't process response.data separately to avoid duplicate audio playback
                    # Audio comes through part.inline_data.data in model_turn.parts
                    
                    # Handle GoAway message (connection will terminate)
                    if hasattr(response, 'go_away') and response.go_away is not None:
                        print(f"⚠️ GoAway received. Time left: {response.go_away.time_left}")
                    
                    # Handle session resumption updates
                    if hasattr(response, 'session_resumption_update') and response.session_resumption_update:
                        update = response.session_resumption_update
                        if update.resumable and update.new_handle:
                            print(f"📝 Session resumption handle: {update.new_handle}")
                    
                    # Put message in queue for synchronous access
                    try:
                        self.message_queue.put_nowait(response)
                    except queue.Full:
                        pass  # Queue full, skip
                        
        except asyncio.CancelledError:
            print("👂 Response receiver cancelled")
        except Exception as e:
            print(f"❌ Error receiving audio: {e}")
            import traceback
            traceback.print_exc()
            if self.on_error_callback:
                self.on_error_callback(e)
    
    async def _play_audio(self):
        """Plays audio from the output queue.
        
        Based on official example: https://ai.google.dev/gemini-api/docs/live?example=mic-stream
        Output format: 16-bit PCM, 24kHz, mono
        
        Plays chunks directly without buffering for lowest latency (matches official example).
        """
        if not self.pyaudio_instance:
            self.pyaudio_instance = pyaudio.PyAudio()
        
        # Open output stream with correct format (16-bit PCM, 24kHz, mono)
        # Use smaller frames_per_buffer for lower latency
        stream = await asyncio.to_thread(
            self.pyaudio_instance.open,
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.OUTPUT_SAMPLE_RATE,
            output=True,
            frames_per_buffer=512,  # Smaller buffer for lower latency
        )
        
        self.audio_output_stream = stream
        print("🔊 Speaker stream started")
        print(f"   Format: {self.FORMAT} (16-bit PCM)")
        print(f"   Sample Rate: {self.OUTPUT_SAMPLE_RATE} Hz")
        print(f"   Channels: {self.CHANNELS} (mono)")
        print(f"   Frames per buffer: 512 (low latency)")
        
        # Play chunks directly without buffering (matches official example)
        while self.is_streaming and self.is_connected:
            try:
                # Get audio chunk from queue (blocks until available)
                bytestream = await self.audio_output_queue.get()
                
                if not bytestream or len(bytestream) == 0:
                    continue
                
                # Write audio directly to speaker (non-blocking async)
                # This matches the official example: await asyncio.to_thread(stream.write, bytestream)
                await asyncio.to_thread(stream.write, bytestream)
                
            except asyncio.CancelledError:
                print("🔊 Audio player cancelled")
                break
            except Exception as e:
                if self.is_streaming:
                    print(f"⚠️ Error playing audio: {e}")
                    import traceback
                    traceback.print_exc()
                break
    
    def _run_async_loop(self):
        """Run the async event loop in a separate thread."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self._run_live_session())
        finally:
            self.loop.close()
    
    def connect(self):
        """Connect to Gemini Live API (synchronous wrapper)."""
        if self.is_connected:
            return
        
        self.async_thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self.async_thread.start()
        
        # Wait a bit for connection
        time.sleep(2)
    
    def start_streaming(self):
        """Start audio streaming."""
        if not self.is_connected:
            raise RuntimeError("Not connected to Gemini Live API")
        
        if self.is_streaming:
            return
        
        self.is_streaming = True
        print("🎤 Audio streaming started")
    
    def stop_streaming(self):
        """Stop audio streaming."""
        self.is_streaming = False
        
        if self.audio_input_stream:
            try:
                self.audio_input_stream.stop_stream()
                self.audio_input_stream.close()
            except:
                pass
            self.audio_input_stream = None
        
        if self.audio_output_stream:
            try:
                self.audio_output_stream.stop_stream()
                self.audio_output_stream.close()
            except:
                pass
            self.audio_output_stream = None
        
        print("🔇 Audio streaming stopped")
    
    def disconnect(self):
        """Disconnect from Gemini Live API."""
        self.stop_streaming()
        self.is_connected = False
        
        if self.session:
            # Session will be closed when exiting the async context
            self.session = None
        
        if self.pyaudio_instance:
            try:
                self.pyaudio_instance.terminate()
            except:
                pass
            self.pyaudio_instance = None
        
        if self.async_thread:
            self.async_thread.join(timeout=2)
        
        print("🔌 Disconnected from Live API")
    
    def send_text(self, text: str):
        """Send text message to the API."""
        if not self.is_connected or not self.session:
            raise RuntimeError("Not connected to Gemini Live API")
        
        if self.loop:
            asyncio.run_coroutine_threadsafe(
                self.session.send_client_content(
                    turns=types.Content(
                        role="user",
                        parts=[types.Part(text=text)]
                    )
                ),
                self.loop
            )
