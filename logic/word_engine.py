import os
from docx import Document

# =========================
# 路径配置
# =========================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOK_DIR = os.path.join(BASE_DIR, "data", "电子书")

# =========================
# 年份 / 期刊
# =========================
def list_years():
    if not os.path.exists(BOOK_DIR):
        return []
    return sorted(
        d.replace("年", "")
        for d in os.listdir(BOOK_DIR)
        if d.endswith("年")
    )

def list_issues(year):
    year_dir = os.path.join(BOOK_DIR, f"{year}年")
    if not os.path.exists(year_dir):
        return []
    return sorted(
        f for f in os.listdir(year_dir)
        if f.endswith(".docx")
    )

def find_doc_path(year, issue):
    return os.path.join(BOOK_DIR, f"{year}年", issue)

# =========================
# Word 加载
# =========================
def load_document(doc_path):
    return Document(doc_path)

# =========================
# 跳过无效前缀（0000...）
# =========================
def is_garbage_prefix(p):
    text = p.text.strip()
    return text and set(text) == {"0"} and len(text) > 20

# =========================
# 标题判断（替换原正则）
# =========================
def is_column_title(p):
    return p.style and p.style.name == "Heading 1"

def is_topic_title(p):
    return p.style and p.style.name == "Heading 2"

# =========================
# 专栏解析（完全按你原逻辑）
# =========================
def parse_columns(doc_path):
    doc = load_document(doc_path)
    columns = []

    started = False
    for p in doc.paragraphs:
        if not started:
            if is_garbage_prefix(p):
                started = True
            continue

        if is_column_title(p):
            columns.append(p.text.strip())

    return columns

# =========================
# 主题解析（按专栏范围）
# =========================
def parse_topics(doc_path, column_title):
    doc = load_document(doc_path)

    started = False
    current_column = None
    topics = []

    for p in doc.paragraphs:
        if not started:
            if is_garbage_prefix(p):
                started = True
            continue

        if is_column_title(p):
            current_column = p.text.strip()
            continue

        if current_column == column_title and is_topic_title(p):
            topics.append(p.text.strip())

    return topics

# =========================
# 获取主题正文（流式）
# =========================
def get_topic_content(doc_path, column_title, topic_title):
    doc = load_document(doc_path)

    started = False
    current_column = None
    current_topic = None
    content = []

    for p in doc.paragraphs:
        if not started:
            if is_garbage_prefix(p):
                started = True
            continue

        if is_column_title(p):
            current_column = p.text.strip()
            current_topic = None
            continue

        if is_topic_title(p):
            current_topic = p.text.strip()
            continue

        if (
            current_column == column_title
            and current_topic == topic_title
            and p.text.strip()
        ):
            content.append(p.text.strip())

    return content

# =========================
# 结构化搜索（同原思路）
# =========================
def structured_search(doc_path, keyword, context_window=2):
    if not keyword:
        return []

    doc = load_document(doc_path)

    started = False
    current_column = None
    current_topic = None
    para_map = []

    for idx, p in enumerate(doc.paragraphs):
        if not started:
            if is_garbage_prefix(p):
                started = True
            continue

        if is_column_title(p):
            current_column = p.text.strip()
            current_topic = None
            continue

        if is_topic_title(p):
            current_topic = p.text.strip()
            continue

        if p.text.strip():
            para_map.append({
                "index": idx,
                "text": p.text.strip(),
                "column": current_column,
                "topic": current_topic
            })

    results = []
    for i, item in enumerate(para_map):
        if keyword in item["text"]:
            start = max(0, i - context_window)
            end = min(len(para_map), i + context_window + 1)
            context = [para_map[j]["text"] for j in range(start, end)]

            results.append({
                "column": item["column"],
                "topic": item["topic"],
                "paragraph": item["text"],
                "context": context
            })

    return results
# =========================
# 对外接口：专栏列表
# =========================
def list_columns(doc_path):
    """
    返回所有专栏（Heading 1）
    """
    return parse_columns(doc_path)

# =========================
# 对外接口：主题列表
# =========================
def list_topics(doc_path, column_title):
    """
    返回指定专栏（Heading 1）下的所有主题（Heading 2）
    """
    return parse_topics(doc_path, column_title)




