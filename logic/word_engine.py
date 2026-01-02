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
# 定位正文起点（跳过 0000...）
# =========================
def find_content_start_index(doc):
    """
    从出现大量 0 的段落之后，才开始读取正文
    """
    for i, p in enumerate(doc.paragraphs):
        if p.text and set(p.text.strip()) == {"0"} and len(p.text.strip()) > 20:
            return i + 1
    return 0

# =========================
# 解析结构（核心）
# =========================
def parse_structure(doc_path):
    """
    返回结构：
    {
        专栏名: [
            {
                "title": 主题名,
                "start": 段落起始索引,
                "end": 段落结束索引
            },
            ...
        ],
        ...
    }
    """
    doc = load_document(doc_path)
    start_idx = find_content_start_index(doc)

    structure = {}
    current_column = None
    current_topic = None

    paragraphs = doc.paragraphs

    for i in range(start_idx, len(paragraphs)):
        p = paragraphs[i]
        text = p.text.strip()
        if not text:
            continue

        style = p.style.name if p.style else ""

        # 标题1 → 专栏
        if style == "Heading 1":
            current_column = text
            structure[current_column] = []
            current_topic = None

        # 标题2 → 主题
        elif style == "Heading 2" and current_column:
            topic = {
                "title": text,
                "start": i,
                "end": None
            }
            structure[current_column].append(topic)
            current_topic = topic

        # 普通正文
        else:
            continue

    # 补齐每个主题的 end
    for col, topics in structure.items():
        for idx, t in enumerate(topics):
            if idx < len(topics) - 1:
                t["end"] = topics[idx + 1]["start"]
            else:
                t["end"] = len(paragraphs)

    return structure

# =========================
# 对外接口
# =========================
def list_columns(doc_path):
    return list(parse_structure(doc_path).keys())

def list_topics(doc_path, column):
    structure = parse_structure(doc_path)
    return [t["title"] for t in structure.get(column, [])]

def get_topic_content(doc_path, column, topic_title):
    doc = load_document(doc_path)
    structure = parse_structure(doc_path)

    topics = structure.get(column, [])
    topic = next(
        (t for t in topics if t["title"] == topic_title),
        None
    )
    if not topic:
        return []

    content = []
    for p in doc.paragraphs[topic["start"] + 1: topic["end"]]:
        if p.style.name.startswith("Heading"):
            continue
        if p.text.strip():
            content.append(p.text.strip())

    return content




