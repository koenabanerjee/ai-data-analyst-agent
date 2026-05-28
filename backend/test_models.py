import google.generativeai as genai

API_KEY = "AIzaSyB4pGDNIGzEfK5VhctkNflPIVy7572nA0M"

genai.configure(api_key=API_KEY)

models = genai.list_models()

for model in models:
    if "generateContent" in model.supported_generation_methods:
        print(model.name)