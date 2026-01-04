import requests

API_URL = "https://api.deepseek.com/v1/chat/completions"
API_KEY = "sk_你的api密钥"  # 直接填入你的 API Key

def ask_ai(question, context):
    """
    基于给定的上下文和用户问题，调用 DeepSeek API 进行分析
    
    Args:
        question (str): 用户的问题
        context (str): 分析的上下文（从专栏内容或自定义文本获取）
    
    Returns:
        str: AI 的分析结果
    """
    # 构建 prompt
    prompt = f"""请基于以下内容回答用户的问题：

【内容】
{context}

【用户问题】
{question}

【要求】
- 用中文回答
- 结构清晰，逻辑严密
- 直接基于提供的内容进行分析
- 如果内容中没有相关信息，请明确说明
- 提供有深度的分析和见解"""

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
    
    try:
        resp = requests.post(
            API_URL,
            json=payload,
            headers=headers,
            timeout=60
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    
    except requests.exceptions.Timeout:
        raise Exception("⏱️ 请求超时，请稍后重试")
    except requests.exceptions.RequestException as e:
        raise Exception(f"API 调用失败：{str(e)}")


def summarize_text(text):
    """文本摘要"""
    return ask_ai("请总结这段内容的核心观点，用 3-5 点概括", text)


def extract_keywords(text):
    """提取关键词"""
    return ask_ai("请从这段内容中提取 5-10 个关键词，并简要解释每个词的含义", text)


def analyze_topic(text):
    """主题分析"""
    return ask_ai("请深入分析这段内容，包括背景、重点和启示", text)
