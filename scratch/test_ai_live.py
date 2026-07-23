import sys
sys.path.insert(0, 'src')
from ai.ollama_client import OllamaClient

def test_ollama_live():
    print("🤖 Testing FinAuditPro Ollama AI Integration...")
    client = OllamaClient()
    prompt = "Summarize key ICAI SA 240 fraud risk factors for Indian statutory audits in 2 bullet points."
    
    print("\n1. Testing Streaming Generation (generate_stream):")
    try:
        chunks = []
        for chunk in client.generate_stream(prompt=prompt):
            print(chunk, end="", flush=True)
            chunks.append(chunk)
        full_text = "".join(chunks)
        if full_text.strip():
            print("\n\n✅ LIVE AI STREAMING SUCCESSFUL!")
        else:
            print("\n\n⚠️ Streaming yielded empty response, trying sync fallback...")
            res = client.generate(prompt=prompt)
            print("Sync Result:", res)
    except Exception as e:
        print(f"\n❌ Ollama Error: {e}")

if __name__ == "__main__":
    test_ollama_live()
