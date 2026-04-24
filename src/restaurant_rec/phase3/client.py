import json
from groq import Groq
from typing import Dict, Any
from ..config import config

def call_llm(prompt: str, system_instruction: str) -> Dict[str, Any]:
    """
    Call the Groq API and return the parsed JSON response.
    """
    if not config.groq_api_key:
        raise ValueError("GROQ_API_KEY not found in configuration or .env file")

    client = Groq(api_key=config.groq_api_key)
    
    # Merge system instruction into the messages
    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": prompt}
    ]

    chat_completion = client.chat.completions.create(
        messages=messages,
        model=config.groq_model_id,
        temperature=config.temperature,
        response_format={"type": "json_object"}
    )

    response_text = chat_completion.choices[0].message.content
    
    try:
        return json.loads(response_text)
    except (json.JSONDecodeError, AttributeError) as e:
        return {
            "summary": f"Error parsing LLM response: {str(e)}",
            "recommendations": []
        }
