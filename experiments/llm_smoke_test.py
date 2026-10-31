from openai import OpenAI
import os

client = OpenAI(
 base_url="https://logfare.ai/v1",
 api_key=os.environ.get("LOGFARE_API_KEY", ""), # from /register
)

response = client.chat.completions.create(
 model="kimi-k2.5",
 messages=[{"role": "user", "content": "Hello!"}],
)
print(response.choices[0].message.content)