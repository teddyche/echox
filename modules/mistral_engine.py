import logging
from llama_cpp import Llama

# Logger config
logger = logging.getLogger("mistral_engine")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

class MistralEngine:
    def __init__(self, model_path="./models/mistral/mistral.gguf"):
        self.model_path = model_path
        logger.info(f"Chargement du modèle Mistral depuis : {model_path}")
        try:
            self.llm = Llama(model_path=model_path, n_ctx=2048, n_threads=4)
            logger.info("Modèle Mistral chargé avec succès.")
        except Exception as e:
            logger.error(f"Erreur de chargement du modèle Mistral : {e}")
            self.llm = None

    def generate(self, prompt: str, max_tokens: int = 200) -> str:
        if not self.llm:
            return "[Erreur: modèle non chargé]"

        # Format spécial pour Mistral instruct-style
        formatted_prompt = f"<s>[INST] {prompt.strip()} [/INST]"

        try:
            logger.info(f"Génération de texte avec Mistral : '{prompt}'")
            output = self.llm(formatted_prompt, max_tokens=max_tokens, stop=["</s>"], echo=False)
            texte = output["choices"][0]["text"].strip()
            logger.info(f"Texte généré : {texte}")
            return texte
        except Exception as e:
            logger.error(f"Erreur de génération avec Mistral : {e}")
            return "[Erreur de génération]"

# Test rapide
if __name__ == "__main__":
    engine = MistralEngine()
    while True:
        prompt = input("🧠 Prompt > ")
        if prompt.lower() in ["exit", "quit"]:
            break
        print("🤖", engine.generate(prompt))

