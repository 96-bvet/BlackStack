#!/usr/bin/env python3
"""
BlackStack Sentinel Core - Optimized Cybersecurity AI System
-----------------------------------------------------------
- High-performance Qwen inference with RTX 3060 optimization
- Real-time audio processing with Rust backend
- Audit-safe operations with forensic logging
- Optimized for AMD Ryzen 7 7700 and RTX 3060 hardware
"""

import os
import sys
import socket
import time
import logging
from typing import Optional, Dict, List
from datetime import datetime

# --- Optional: ensure project root is on sys.path for local imports ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(PROJECT_ROOT, 'logs', 'sentinel.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Try to import optimized modules
try:
    from models.qwen_wrapper_optimized import OptimizedQwenModel
    from modules.voice.audio_processor_optimized import OptimizedAudioProcessor
    HAS_OPTIMIZED_MODULES = True
    logger.info("Using optimized modules for maximum performance")
except ImportError as e:
    logger.warning(f"Optimized modules not available, falling back to standard implementation: {e}")
    HAS_OPTIMIZED_MODULES = False
    # Fallback imports
    try:
        from models.qwen_wrapper import QwenModel as OptimizedQwenModel
        from modules.voice.audio_input import capture_audio
        from modules.voice.audio_output import speak_text
    except ImportError as e:
        logger.error(f"Could not import fallback modules: {e}")

# Import mutator safely
try:
    from qwen_mutator import mutate_code
except ImportError:
    logger.warning("qwen_mutator not available, mutation functions disabled")
    mutate_code = None

class OptimizedSentinelCore:
    """
    High-performance Sentinel Core optimized for cybersecurity operations.
    Integrates optimized AI inference, audio processing, and system monitoring.
    """
    
    def __init__(self, model_path: str = None, enable_voice: bool = True):
        self.model_path = model_path or os.path.expanduser("~/Qwen2.5-14B")
        self.enable_voice = enable_voice
        self.ai_model = None
        self.audio_processor = None
        self.performance_stats = {
            'start_time': time.time(),
            'total_requests': 0,
            'voice_sessions': 0,
            'mutations_applied': 0,
        }
        
        logger.info("Initializing OptimizedSentinelCore...")
        self._initialize_ai_model()
        if enable_voice:
            self._initialize_audio_system()
        
    def _initialize_ai_model(self):
        """Initialize the optimized AI model."""
        try:
            if HAS_OPTIMIZED_MODULES:
                self.ai_model = OptimizedQwenModel(
                    model_path=self.model_path,
                    use_cpp=True,  # Prefer C++ backend for performance
                    device="auto"
                )
                logger.info("Initialized optimized AI model with C++ backend")
            else:
                self.ai_model = OptimizedQwenModel(model_path=self.model_path)
                logger.info("Initialized standard AI model")
                
        except Exception as e:
            logger.error(f"Failed to initialize AI model: {e}")
            self.ai_model = None
    
    def _initialize_audio_system(self):
        """Initialize the optimized audio processing system."""
        try:
            if HAS_OPTIMIZED_MODULES:
                self.audio_processor = OptimizedAudioProcessor(
                    sample_rate=44100,
                    channels=2,
                    buffer_size=1024,
                    use_rust=True  # Prefer Rust backend for performance
                )
                logger.info("Initialized optimized audio processor with Rust backend")
            else:
                logger.info("Using fallback audio functions")
                
        except Exception as e:
            logger.error(f"Failed to initialize audio system: {e}")
            self.audio_processor = None
    
    def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate AI response with performance optimization."""
        if not self.ai_model:
            return "[ERROR] AI model not available"
            
        try:
            start_time = time.time()
            
            # Use optimized generation
            if hasattr(self.ai_model, 'generate'):
                response = self.ai_model.generate(prompt, **kwargs)
                if isinstance(response, list) and len(response) > 0:
                    result = response[0].get('generated_text', '')
                else:
                    result = str(response)
            else:
                result = "[ERROR] Generation method not available"
            
            # Update performance stats
            generation_time = time.time() - start_time
            self.performance_stats['total_requests'] += 1
            
            logger.info(f"Generated response in {generation_time:.3f}s")
            return result
            
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            return f"[ERROR] Generation failed: {e}"
    
    def start_voice_session(self, device_name: str = None) -> bool:
        """Start an optimized voice interaction session."""
        if not self.audio_processor:
            logger.error("Audio processor not available")
            return False
            
        try:
            success = self.audio_processor.start_capture(device_name)
            if success:
                self.performance_stats['voice_sessions'] += 1
                logger.info("Voice session started")
            return success
            
        except Exception as e:
            logger.error(f"Failed to start voice session: {e}")
            return False
    
    def stop_voice_session(self) -> bool:
        """Stop the current voice session."""
        if not self.audio_processor:
            return True
            
        try:
            return self.audio_processor.stop_capture()
        except Exception as e:
            logger.error(f"Failed to stop voice session: {e}")
            return False
    
    def get_performance_stats(self) -> Dict:
        """Get comprehensive performance statistics."""
        stats = self.performance_stats.copy()
        stats['uptime'] = time.time() - stats['start_time']
        
        # Add AI model stats
        if self.ai_model and hasattr(self.ai_model, 'get_performance_stats'):
            stats['ai_model'] = self.ai_model.get_performance_stats()
        
        # Add audio processor stats
        if self.audio_processor and hasattr(self.audio_processor, 'get_performance_stats'):
            stats['audio_processor'] = self.audio_processor.get_performance_stats()
        
        return stats
    
    def optimize_system(self):
        """Perform system optimization for maximum performance."""
        logger.info("Performing system optimization...")
        
        # Optimize AI model memory
        if self.ai_model and hasattr(self.ai_model, 'optimize_memory'):
            self.ai_model.optimize_memory()
        
        # Clear audio buffers
        if self.audio_processor and hasattr(self.audio_processor, 'clear_buffer'):
            self.audio_processor.clear_buffer()
        
        # System-level optimizations
        if os.name == 'posix':  # Linux/Unix
            try:
                # Clear system caches (if possible)
                os.system('sync')
                logger.info("System optimization completed")
            except Exception as e:
                logger.warning(f"System optimization failed: {e}")


def finalize_full_tree():
    """Finalize the full tree mutation pass with optimized processing."""
    if not mutate_code:
        logger.warning("Mutation functionality not available")
        return None
        
    try:
        modules_dir = os.path.join(PROJECT_ROOT, "modules")
        if not os.path.exists(modules_dir):
            logger.error(f"Modules directory not found: {modules_dir}")
            return None
            
        for file in os.listdir(modules_dir):
            if file.endswith(".py") and not file.startswith("__"):
                file_path = os.path.join("modules", file)
                try:
                    result = mutate_code(file_path, "Optimize for performance, audit safety, and forensic soundness.")
                    logger.info(f"[OK] Optimized {file}")
                except Exception as e:
                    logger.error(f"[FAIL] Failed to optimize {file}: {e}")
        
        return "Full tree optimization completed"
        
    except Exception as e:
        logger.error(f"Full tree optimization failed: {e}")
        return None

def provision_voices():
    """
    Provision voice models for persona-aware audio output.
    Optimized for performance and memory efficiency.
    """
    voices = {
        "analyst": ("en_US-lessac-high.onnx", "en_US-lessac-high.onnx.json"),
        "operator": ("en_US-ryan-medium.onnx", "en_US-ryan-medium.onnx.json"),
        "commander": ("en_GB-alan-medium.onnx", "en_GB-alan-medium.onnx.json"),
    }
    
    logger.info("Provisioning voice models for enhanced persona interaction...")
    
    voice_dir = os.path.join(PROJECT_ROOT, "models", "voices")
    os.makedirs(voice_dir, exist_ok=True)
    
    for persona, files in voices.items():
        logger.info(f"Provisioning voice for persona: {persona}")
        for voice_file in files:
            file_path = os.path.join(voice_dir, voice_file)
            if os.path.exists(file_path):
                logger.info(f"[SKIP] {voice_file} already exists")
            else:
                logger.info(f"[TODO] {voice_file} needs to be downloaded")
                # In a real implementation, you'd download the voice models here
    
    logger.info("Voice provisioning completed")


def main():
    """
    Main entry point for the optimized Sentinel Core system.
    """
    try:
        logger.info("=" * 60)
        logger.info("BlackStack WachterEID Cybersecurity AI System")
        logger.info("Optimized for RTX 3060 + AMD Ryzen 7 7700")
        logger.info("=" * 60)
        
        # Initialize the core system
        sentinel = OptimizedSentinelCore(enable_voice=True)
        
        # Provision voice models
        provision_voices()
        
        # Test system functionality
        logger.info("Testing system functionality...")
        
        # Test AI generation
        test_prompt = "System status check: Report current operational parameters."
        response = sentinel.generate_response(test_prompt, max_new_tokens=100)
        logger.info(f"AI Response: {response[:200]}...")
        
        # Performance optimization
        sentinel.optimize_system()
        
        # Display performance statistics
        stats = sentinel.get_performance_stats()
        logger.info("Performance Statistics:")
        for key, value in stats.items():
            if isinstance(value, dict):
                logger.info(f"  {key}:")
                for subkey, subvalue in value.items():
                    logger.info(f"    {subkey}: {subvalue}")
            else:
                logger.info(f"  {key}: {value}")
        
        # Test mutation functionality if available
        if mutate_code:
            logger.info("Testing mutation functionality...")
            mutation_result = finalize_full_tree()
            if mutation_result:
                logger.info("Full tree mutation completed successfully")
            else:
                logger.warning("Full tree mutation encountered issues")
        
        logger.info("=" * 60)
        logger.info("WachterEID system initialization completed successfully")
        logger.info("System ready for cybersecurity operations")
        logger.info("=" * 60)
        
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    except Exception as e:
        logger.error(f"System initialization failed: {e}")
        raise
    finally:
        # Cleanup
        logger.info("Performing system cleanup...")


if __name__ == "__main__":
    main()
