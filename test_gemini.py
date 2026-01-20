import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

load_dotenv()

def test_gemini():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ No API Key found")
        return

    try:
        # Trying gemini-3-pro-preview as requested
        llm = ChatGoogleGenerativeAI(
            model="gemini-3-pro-preview", 
            google_api_key=api_key,
            temperature=0.7
        )
        print("Sending request to gemini-3-pro-preview...")
        
        msg = [HumanMessage(content="Hello!")]
        response = llm.invoke(msg)
        
        print("\n✅ API Success!")
        print(f"Response: {response.content}")
        
    except Exception as e:
        print(f"\n❌ API Failed: {e}")

if __name__ == "__main__":
    test_gemini()
