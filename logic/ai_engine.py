import os
import requests

# =========================
# AI 配置
# =========================
AI_PROVIDER = "openai"   # 预留，后期可换
API_ENV_KEY = "OPENAI_API_KEY"

API_URL = "https://api.openai.com/v1/chat/completions"
MODEL = "gpt-4o-mini"    # 稳定 + 成本低（你也可以换）

# =========================
# 基础工具
# =========================
def _get_api_key():
    key = os.getenv(API_ENV_KEY)
    if not key:
        raise RuntimeError(
            "未检测到 OPENAI_API_KEY 环境变量"
        )
    return key


def _call_llm(messages, temperature=0.3, max_tokens=800):
    headers = {
        "Authorization": f"Bearer {_get_api_key()}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    r = requests.post(API_URL, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


# =========================
# 对外功能接口
# =========================
def summarize_text(text):
    """
    段落 / 主题摘要
    """
    messages = [
        {"role": "system", "content": "你是一个严谨的学术文献助理"},
        {
            "role": "user",
            "content": f"请对下面内容做不超过200字的学术摘要：\n{text}"
        }
    ]
    return _call_llm(messages)


def analyze_topic(text):
    """
    主题分析（研究价值 / 观点 / 结论）
    """
    messages = [
        {"role": "system", "content": "你是科研助理，擅长文献分析"},
        {
            "role": "user",
            "content": (
                "请从【研究主题】【核心观点】【结论】三个方面分析下面内容：\n"
                f"{text}"
            )
        }
    ]
    return _call_llm(messages)


def extract_keywords(text):
    """
    关键词提取
    """
    messages = [
        {"role": "system", "content": "你是信息抽取助手"},
        {
            "role": "user",
            "content": (
                "请提取下面内容中最重要的5-8个关键词，用顿号分隔：\n"
                f"{text}"
            )
        }
    ]
    return _call_llm(messages, temperature=0.2)
