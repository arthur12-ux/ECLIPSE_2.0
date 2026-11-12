"""llm_test_connection.py

Quick script to verify connectivity to an OpenAI-compatible LLM (LM Studio or OpenAI).

Usage:
    python llm_test_connection.py

Environment:
    Set environment variables like OPENAI_API_BASE and OPENAI_API_KEY if needed.
"""

import os
from openai import OpenAI

# Get endpoint and key from environment
api_base = os.environ.get("OPENAI_API_BASE", "http://localhost:1234/v1")
api_key = os.environ.get("OPENAI_API_KEY", "not-needed")
model = os.environ.get("OPENAI_MODEL", "openai/gpt-oss-20b")

client = OpenAI(base_url=api_base, api_key=api_key)

messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Say hello and tell me what model you are."}
]

try:
    result = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.0,
        max_tokens=50
    )
    print("LLM response:", result.choices[0].message.content)
    print("Model used:", getattr(result, "model", None))
except Exception as e:
    print("LLM call failed:", e)
