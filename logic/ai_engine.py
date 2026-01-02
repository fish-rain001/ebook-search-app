import requests

API_URL = "https://api.deepseek.com/v1/chat/completions"
API_KEY = "⚠️这里换成你的 key"

def ask_ai(question, context):
    prompt = f"""
请基于以下内容回答用户问题：

--- 内容 ---
{context}
--- 结束 ---

问题：{question}

要求：
- 中文
- 结构清晰
- 有分析深度
"""

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 2000
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    resp = requests.post(API_URL, json=payload, headers=headers, timeout=60)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


