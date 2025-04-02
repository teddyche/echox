from transformers import AutoModelForCausalLM, AutoTokenizer

model_name = "distilgpt2"
save_path = "./models/distilgpt2_model"

# Charger le modèle/tokenizer depuis Hugging Face (ou le cache local s’il existe)
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# Sauvegarder localement
tokenizer.save_pretrained(save_path)
model.save_pretrained(save_path)

print(f"Modèle DistilGPT-2 sauvegardé dans : {save_path}")

