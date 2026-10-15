import requests

url = "http://localhost:11434/api/generate"

data = {
    "model": "llama3.2:3b",
    "prompt": "Write an Instagram caption for a cotton shirt priced at Rs 599.",
    "stream": False
}

try:
    response = requests.post(url, json=data, timeout=180)
    response.raise_for_status()

    result = response.json()
    print("\nAI Generated Caption:\n")
    print(result["response"])

except requests.RequestException as error:
    print("Ollama connection error:", error)