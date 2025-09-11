"""
Optimized audio processing module for BlackStack WachterEID
Uses Rust backend for high-performance audio processing when available
"""

import logging
import time
import numpy as np
from typing import Optional, Tuple, List
import threading
import queue

# Try to import the Rust backend
try:
    import audio_processor
    HAS_RUST_BACKEND = True
    logging.info("[AudioProcessor] Using optimized Rust backend")
except ImportError:
    HAS_RUST_BACKEND = False
    logging.info("[AudioProcessor] Using Python backend (Rust not available)")
    
    # Fallback imports for Python backend
    try:
        import pyaudio
        import wave
        import audioop
        HAS_PYAUDIO = True
    except ImportError:
        HAS_PYAUDIO = False
        logging.warning("[AudioProcessor] PyAudio not available, limited functionality")

class OptimizedAudioProcessor:
    """
    High-performance audio processor optimized for real-time cybersecurity applications.
    Automatically selects between Rust and Python implementations.
    """
    
    def __init__(self, sample_rate: int = 44100, channels: int = 2, 
                 buffer_size: int = 1024, use_rust: bool = None):
        self.sample_rate = sample_rate
        self.channels = channels
        self.buffer_size = buffer_size
        self.use_rust = use_rust if use_rust is not None else HAS_RUST_BACKEND
        
        # Audio processor instance
        self.rust_processor = None
        self.py_stream = None
        self.py_audio = None
        
        # Recording state
        self.is_recording = False
        self.audio_buffer = queue.Queue(maxsize=1000)
        self.record_thread = None
        
        # Performance monitoring
        self.total_processed = 0
        self.processing_time = 0.0
        
        # Initialize the appropriate backend
        if self.use_rust and HAS_RUST_BACKEND:
            self._init_rust_backend()
        else:
            self._init_python_backend()
            
        logging.info(f"[AudioProcessor] Initialized with {'Rust' if self.use_rust else 'Python'} backend")
    
    def _init_rust_backend(self):
        """Initialize the Rust backend."""
        try:
            # Configure for optimal performance
            config = {
                'sample_rate': self.sample_rate,
                'channels': self.channels,
                'buffer_size': self.buffer_size,
                'enable_noise_gate': True,
                'noise_threshold': 0.01,
                'enable_compressor': True,
                'compression_ratio': 4.0,
            }
            
            self.rust_processor = audio_processor.AudioProcessor(config)
            
        except Exception as e:
            logging.error(f"[AudioProcessor] Failed to initialize Rust backend: {e}")
            self.use_rust = False
            self._init_python_backend()
    
    def _init_python_backend(self):
        """Initialize the Python backend."""
        if not HAS_PYAUDIO:
            logging.error("[AudioProcessor] PyAudio not available for Python backend")
            return
            
        try:
            self.py_audio = pyaudio.PyAudio()
        except Exception as e:
            logging.error(f"[AudioProcessor] Failed to initialize PyAudio: {e}")
    
    def start_capture(self, device_name: Optional[str] = None) -> bool:
        """Start audio capture with the specified device."""
        if self.is_recording:
            logging.warning("[AudioProcessor] Already recording")
            return False
            
        try:
            if self.use_rust and self.rust_processor:
                self.rust_processor.start_capture(device_name)
                self.is_recording = True
            else:
                self._start_python_capture(device_name)
                
            logging.info(f"[AudioProcessor] Started capture with {'Rust' if self.use_rust else 'Python'} backend")
            return True
            
        except Exception as e:
            logging.error(f"[AudioProcessor] Failed to start capture: {e}")
            return False
    
    def _start_python_capture(self, device_name: Optional[str] = None):
        """Start capture using Python backend."""
        if not self.py_audio:
            raise RuntimeError("PyAudio not initialized")
            
        # Find device
        device_index = None
        if device_name:
            for i in range(self.py_audio.get_device_count()):
                info = self.py_audio.get_device_info_by_index(i)
                if device_name.lower() in info['name'].lower():
                    device_index = i
                    break
        
        # Open stream
        self.py_stream = self.py_audio.open(
            format=pyaudio.paFloat32,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=self.buffer_size,
            stream_callback=self._python_audio_callback
        )
        
        self.py_stream.start_stream()
        self.is_recording = True
    
    def _python_audio_callback(self, in_data, frame_count, time_info, status):
        """Callback for Python audio stream."""
        if self.is_recording:
            # Convert bytes to numpy array
            audio_data = np.frombuffer(in_data, dtype=np.float32)
            
            # Basic audio processing
            processed_data = self._process_audio_python(audio_data)
            
            # Add to buffer
            try:
                self.audio_buffer.put(processed_data, block=False)
            except queue.Full:
                # Buffer is full, drop oldest data
                try:
                    self.audio_buffer.get(block=False)
                    self.audio_buffer.put(processed_data, block=False)
                except queue.Empty:
                    pass
        
        return (None, pyaudio.paContinue)
    
    def _process_audio_python(self, audio_data: np.ndarray) -> np.ndarray:
        """Process audio data using Python (simplified version of Rust processing)."""
        # Noise gate
        noise_threshold = 0.01
        audio_data[np.abs(audio_data) < noise_threshold] = 0.0
        
        # Simple compressor
        threshold = 0.7
        compression_ratio = 4.0
        mask = np.abs(audio_data) > threshold
        excess = np.abs(audio_data[mask]) - threshold
        compressed_excess = excess / compression_ratio
        audio_data[mask] = np.sign(audio_data[mask]) * (threshold + compressed_excess)
        
        return audio_data
    
    def stop_capture(self) -> bool:
        """Stop audio capture."""
        if not self.is_recording:
            return True
            
        try:
            self.is_recording = False
            
            if self.use_rust and self.rust_processor:
                self.rust_processor.stop_capture()
            elif self.py_stream:
                self.py_stream.stop_stream()
                self.py_stream.close()
                self.py_stream = None
                
            logging.info("[AudioProcessor] Stopped capture")
            return True
            
        except Exception as e:
            logging.error(f"[AudioProcessor] Failed to stop capture: {e}")
            return False
    
    def get_audio_data(self) -> Optional[bytes]:
        """Get captured audio data."""
        if self.use_rust and self.rust_processor:
            # Rust backend returns Python bytes object
            return self.rust_processor.get_audio_data()
        else:
            # Python backend - collect from queue
            audio_chunks = []
            while not self.audio_buffer.empty():
                try:
                    chunk = self.audio_buffer.get(block=False)
                    audio_chunks.append(chunk)
                except queue.Empty:
                    break
            
            if audio_chunks:
                combined = np.concatenate(audio_chunks)
                return combined.tobytes()
            return b''
    
    def get_audio_level(self) -> float:
        """Get current audio level (RMS)."""
        if self.use_rust and self.rust_processor:
            return self.rust_processor.analyze_audio()
        else:
            # Python backend - analyze current buffer
            if self.audio_buffer.empty():
                return 0.0
                
            try:
                # Peek at the most recent chunk
                chunk = self.audio_buffer.get(block=False)
                self.audio_buffer.put(chunk, block=False)  # Put it back
                rms = np.sqrt(np.mean(chunk ** 2))
                return float(rms)
            except (queue.Empty, queue.Full):
                return 0.0
    
    def clear_buffer(self):
        """Clear the audio buffer."""
        if self.use_rust and self.rust_processor:
            self.rust_processor.clear_buffer()
        else:
            # Clear Python queue
            while not self.audio_buffer.empty():
                try:
                    self.audio_buffer.get(block=False)
                except queue.Empty:
                    break
    
    def get_buffer_info(self) -> dict:
        """Get buffer information and statistics."""
        info = {
            'backend': 'Rust' if self.use_rust else 'Python',
            'is_recording': self.is_recording,
            'sample_rate': self.sample_rate,
            'channels': self.channels,
            'buffer_size': self.buffer_size,
            'total_processed': self.total_processed,
        }
        
        if self.use_rust and self.rust_processor:
            info.update({
                'buffer_length': self.rust_processor.get_buffer_length(),
                'audio_level': self.rust_processor.analyze_audio(),
            })
        else:
            info.update({
                'buffer_length': self.audio_buffer.qsize(),
                'audio_level': self.get_audio_level(),
            })
        
        return info
    
    def process_file(self, input_file: str, output_file: str) -> bool:
        """Process an audio file (batch processing)."""
        try:
            start_time = time.time()
            
            # Load audio file
            with wave.open(input_file, 'rb') as wav_file:
                frames = wav_file.readframes(-1)
                sample_rate = wav_file.getframerate()
                channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
            
            # Convert to float32
            if sample_width == 2:
                audio_data = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
            else:
                audio_data = np.frombuffer(frames, dtype=np.float32)
            
            # Process audio
            if self.use_rust:
                # For file processing, we'd need to add this to the Rust module
                # For now, use Python processing
                processed_data = self._process_audio_python(audio_data)
            else:
                processed_data = self._process_audio_python(audio_data)
            
            # Convert back to int16
            processed_int16 = (processed_data * 32767).astype(np.int16)
            
            # Save processed audio
            with wave.open(output_file, 'wb') as wav_file:
                wav_file.setnchannels(channels)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(processed_int16.tobytes())
            
            # Update performance metrics
            processing_time = time.time() - start_time
            self.processing_time += processing_time
            self.total_processed += 1
            
            logging.info(f"[AudioProcessor] Processed {input_file} -> {output_file} in {processing_time:.3f}s")
            return True
            
        except Exception as e:
            logging.error(f"[AudioProcessor] Failed to process file {input_file}: {e}")
            return False
    
    def get_performance_stats(self) -> dict:
        """Get performance statistics."""
        return {
            'backend': 'Rust' if self.use_rust else 'Python',
            'total_processed': self.total_processed,
            'processing_time': self.processing_time,
            'average_time': self.processing_time / max(1, self.total_processed),
        }
    
    def cleanup(self):
        """Clean up resources."""
        self.stop_capture()
        
        if self.py_audio:
            self.py_audio.terminate()
            self.py_audio = None
    
    def __del__(self):
        """Destructor."""
        self.cleanup()


# For backward compatibility
class AudioProcessor(OptimizedAudioProcessor):
    """Backward compatibility wrapper."""
    pass


def list_audio_devices() -> List[dict]:
    """List available audio input devices."""
    devices = []
    
    if HAS_PYAUDIO:
        try:
            pa = pyaudio.PyAudio()
            for i in range(pa.get_device_count()):
                info = pa.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    devices.append({
                        'index': i,
                        'name': info['name'],
                        'channels': info['maxInputChannels'],
                        'sample_rate': int(info['defaultSampleRate']),
                    })
            pa.terminate()
        except Exception as e:
            logging.error(f"Failed to list audio devices: {e}")
    
    return devices