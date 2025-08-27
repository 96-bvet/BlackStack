import importlib.util
import os

def load_persona_engine(persona):
    path = os.path.expanduser(f"~/BlackStack/WachterEID/runtime/persona_variants/{persona.lower()}_v2.py")
    spec = importlib.util.spec_from_file_location("deepseek_v2", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.run_deepseek_v2
