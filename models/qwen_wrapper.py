# models/qwen_wrapper.py

import os, torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from registry import resolve_persona_by_module
from runtime.router.tone_router import inject_tone
from runtime.persona_variants.auditpersona_v2 import gatekeeper_check

class QwenModel:
    def __init__(self, model_path="/home/blackhawk63/Qwen2.5-14B"):
        self.model_path = model_path
        self.tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)

        self.quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4"
        )

        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            trust_remote_code=True,
            device_map="auto",
            quantization_config=self.quant_config,
            max_memory={"cuda:0": "8GiB", "cpu": "32GiB"}
        )

        self.model.eval()
        print(f"[QwenModel] Resident core initialized from: {model_path}")

    def generate(self, prompt, max_new_tokens=1024, do_sample=True):
        module_path = "models/qwen_wrapper.py"
        persona_data = resolve_persona_by_module(module_path)
        tone = persona_data["tone_profile"]

        if not gatekeeper_check(module_path):
            raise PermissionError(f"[Gatekeeper] Mutation blocked for {module_path}")

        enriched_prompt = inject_tone(prompt, tone)

        inputs = self.tokenizer(enriched_prompt, return_tensors="pt")
        input_ids = inputs["input_ids"].to(self.model.device)
        attention_mask = inputs["attention_mask"].to(self.model.device)

        with torch.no_grad():
            outputs = self.model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                max_new_tokens=max_new_tokens,
                do_sample=do_sample,
                temperature=0.6,
                top_p=0.95,
                top_k=20
            )

        return [{"generated_text": self.tokenizer.decode(outputs[0], skip_special_tokens=True)}]
