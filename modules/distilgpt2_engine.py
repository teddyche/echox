import logging
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# Configuration du logger
logger = logging.getLogger("distilgpt2_engine")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

class DistilGPT2Engine:
    def __init__(self, model_path="./models/distilgpt2_model"):
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        self.device = torch.device("cpu")
        self.load_model()

    def load_model(self):
        logger.info(f"Chargement du modèle depuis '{self.model_path}' sur {self.device}...")
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self.model = AutoModelForCausalLM.from_pretrained(self.model_path)
            self.model.to(self.device)
            logger.info("Modèle chargé avec succès.")
        except Exception as e:
            logger.error(f"Erreur lors du chargement du modèle : {e}")

    def generate(self, prompt: str, max_length: int = 150) -> str:
        logger.info(f"Génération de texte pour le prompt : '{prompt}'")
        try:
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            outputs = self.model.generate(
                **inputs,
                max_length=max_length,
                pad_token_id=self.tokenizer.eos_token_id,
                temperature=0.7,
                top_k=50,
                top_p=0.95,
                repetition_penalty=1.2,
                do_sample=True
            )
            result = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            logger.info(f"Texte généré : {result}")
            return result
        except Exception as e:
            logger.error(f"Erreur lors de la génération du texte : {e}")
            return "[Erreur de génération]"

# Exemple d'utilisation autonome
if __name__ == "__main__":
    engine = DistilGPT2Engine()
    prompt = "Explique le concept d'entropie en physique."
    print(engine.generate(prompt))

