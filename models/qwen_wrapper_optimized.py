# Optimized Qwen wrapper with fallback support
# Uses C++ implementation when available, falls back to Python

import os
import torch
import logging
from typing import List, Optional, Union
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

# Try to import the optimized C++ implementation
try:
    import qwen_inference_cpp
    HAS_CPP_BACKEND = True
    logging.info("[QwenWrapper] Using optimized C++ backend")
except ImportError:
    HAS_CPP_BACKEND = False
    logging.info("[QwenWrapper] Using Python backend (C++ not available)")

from registry import resolve_persona_by_module
from runtime.router.tone_router import inject_tone
from runtime.persona_variants.auditpersona_v2 import gatekeeper_check

class OptimizedQwenModel:
    """
    High-performance Qwen model wrapper optimized for RTX 3060 and Ryzen 7 7700.
    Automatically selects between C++ and Python implementations based on availability.
    """
    
    def __init__(self, model_path: str = "/home/blackhawk63/Qwen2.5-14B", 
                 use_cpp: bool = None, device: str = "auto"):
        self.model_path = model_path
        self.device_str = device
        self.use_cpp = use_cpp if use_cpp is not None else HAS_CPP_BACKEND
        self.cpp_engine = None
        self.py_model = None
        self.tokenizer = None
        
        # Performance monitoring
        self.total_requests = 0
        self.total_time = 0.0
        
        # Load the appropriate backend
        if self.use_cpp and HAS_CPP_BACKEND:
            self._init_cpp_backend()
        else:
            self._init_python_backend()
            
        # Always load tokenizer for compatibility
        self._init_tokenizer()
        
        logging.info(f"[QwenModel] Initialized with {'C++' if self.use_cpp else 'Python'} backend")
    
    def _init_cpp_backend(self):
        """Initialize the C++ backend."""
        try:
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.cpp_engine = qwen_inference_cpp.QwenInferenceEngine(
                self.model_path, device
            )
            
            # Optimize for the specific hardware
            if torch.cuda.is_available():
                # RTX 3060 optimization - balance between throughput and memory
                gpu_memory = torch.cuda.get_device_properties(0).total_memory
                if gpu_memory <= 12 * 1024**3:  # 12GB or less
                    logging.info("[QwenModel] Optimizing for RTX 3060 (12GB VRAM)")
                    self.cpp_engine.optimize_for_latency()
                else:
                    self.cpp_engine.optimize_for_throughput()
                    
        except Exception as e:
            logging.error(f"[QwenModel] Failed to initialize C++ backend: {e}")
            self.use_cpp = False
            self._init_python_backend()
    
    def _init_python_backend(self):
        """Initialize the Python backend with optimizations."""
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_path, trust_remote_code=True
        )
        
        # Optimized quantization config for RTX 3060
        self.quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4"
        )
        
        # Memory-optimized loading
        max_memory = {"cuda:0": "10GiB", "cpu": "32GiB"}  # Reserve 2GB for other processes
        
        self.py_model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            trust_remote_code=True,
            device_map="auto",
            quantization_config=self.quant_config,
            max_memory=max_memory,
            torch_dtype=torch.float16,
            low_cpu_mem_usage=True
        )
        
        self.py_model.eval()
        
        # Enable optimizations
        if hasattr(self.py_model, 'gradient_checkpointing_enable'):
            self.py_model.gradient_checkpointing_enable()
            
        # Compile model for better performance on modern CPUs
        if hasattr(torch, 'compile') and torch.cuda.is_available():
            try:
                self.py_model = torch.compile(self.py_model, mode="reduce-overhead")
                logging.info("[QwenModel] Model compiled for optimization")
            except Exception as e:
                logging.warning(f"[QwenModel] Failed to compile model: {e}")
    
    def _init_tokenizer(self):
        """Initialize tokenizer if not already done."""
        if self.tokenizer is None:
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path, trust_remote_code=True
            )
    
    def generate(self, prompt: str, max_new_tokens: int = 1024, 
                do_sample: bool = True, temperature: float = 0.6,
                top_p: float = 0.95, top_k: int = 20, **kwargs) -> List[dict]:
        """
        Generate text using the most appropriate backend.
        
        Args:
            prompt: Input text prompt
            max_new_tokens: Maximum tokens to generate
            do_sample: Whether to use sampling
            temperature: Sampling temperature
            top_p: Top-p (nucleus) sampling parameter
            top_k: Top-k sampling parameter
            
        Returns:
            List of generation results compatible with HuggingFace format
        """
        import time
        start_time = time.time()
        
        # Apply persona and gatekeeper checks
        module_path = "models/qwen_wrapper.py"
        
        try:
            persona_data = resolve_persona_by_module(module_path)
            tone = persona_data.get("tone_profile", "neutral")
            
            if not gatekeeper_check(module_path):
                raise PermissionError(f"[Gatekeeper] Generation blocked for {module_path}")
                
            enriched_prompt = inject_tone(prompt, tone)
        except Exception as e:
            logging.warning(f"[QwenModel] Persona/gatekeeper error: {e}, using original prompt")
            enriched_prompt = prompt
        
        # Generate using the appropriate backend
        if self.use_cpp and self.cpp_engine:
            result_text = self._generate_cpp(enriched_prompt, max_new_tokens, 
                                           temperature, top_p, top_k, do_sample)
        else:
            result_text = self._generate_python(enriched_prompt, max_new_tokens,
                                              temperature, top_p, top_k, do_sample)
        
        # Update performance metrics
        end_time = time.time()
        self.total_requests += 1
        self.total_time += (end_time - start_time)
        
        return [{"generated_text": result_text}]
    
    def _generate_cpp(self, prompt: str, max_tokens: int, temperature: float,
                     top_p: float, top_k: int, do_sample: bool) -> str:
        """Generate using C++ backend."""
        return self.cpp_engine.generate_sync(
            prompt, max_tokens, temperature, top_p, top_k, do_sample
        )
    
    def _generate_python(self, prompt: str, max_new_tokens: int, temperature: float,
                        top_p: float, top_k: int, do_sample: bool) -> str:
        """Generate using Python backend."""
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)
        input_ids = inputs["input_ids"].to(self.py_model.device)
        attention_mask = inputs["attention_mask"].to(self.py_model.device)
        
        # Generation parameters optimized for quality and speed
        generation_config = {
            "max_new_tokens": max_new_tokens,
            "do_sample": do_sample,
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "pad_token_id": self.tokenizer.eos_token_id,
            "eos_token_id": self.tokenizer.eos_token_id,
            "use_cache": True,
        }
        
        with torch.no_grad():
            # Use optimized generation
            if hasattr(self.py_model, 'generate'):
                outputs = self.py_model.generate(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    **generation_config
                )
            else:
                # Fallback for older versions
                outputs = self.py_model(input_ids)
                
        # Decode only the new tokens
        new_tokens = outputs[0][input_ids.shape[1]:]
        result = self.tokenizer.decode(new_tokens, skip_special_tokens=True)
        
        return result
    
    def generate_batch(self, prompts: List[str], **kwargs) -> List[str]:
        """Generate text for multiple prompts efficiently."""
        if self.use_cpp and self.cpp_engine:
            return self.cpp_engine.generate_batch(prompts, **kwargs)
        else:
            # Fallback to sequential processing for Python backend
            return [self.generate(prompt, **kwargs)[0]["generated_text"] for prompt in prompts]
    
    def get_performance_stats(self) -> dict:
        """Get performance statistics."""
        stats = {
            "backend": "C++" if self.use_cpp else "Python",
            "total_requests": self.total_requests,
            "average_time": self.total_time / max(1, self.total_requests),
            "total_time": self.total_time,
        }
        
        if self.use_cpp and self.cpp_engine:
            stats.update({
                "cpp_total_requests": self.cpp_engine.get_total_requests(),
                "cpp_average_latency": self.cpp_engine.get_average_latency(),
                "queue_size": self.cpp_engine.get_queue_size(),
                "available_memory": self.cpp_engine.get_available_memory(),
            })
        
        return stats
    
    def optimize_memory(self):
        """Optimize memory usage."""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
        if self.use_cpp and self.cpp_engine:
            # C++ backend handles its own memory optimization
            pass
        elif self.py_model:
            # For Python backend, we can try to clear some caches
            if hasattr(self.py_model, 'gradient_checkpointing_enable'):
                self.py_model.gradient_checkpointing_enable()


# Backward compatibility - maintain the original class name
class QwenModel(OptimizedQwenModel):
    """Backward compatibility wrapper."""
    pass