import os
import re
import glob
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

    issues = []
    for f in os.listdir(year_dir):
        if f.endswith(".docx"):
            issues.append(f)
    return sorted(issues)

def find_doc_path(year, issue):
    return os.path.join(BOOK_DIR, f"{year}年", issue)

# =========================
# Word 加载
# =========================
def load_document(doc_path):
    return Document(doc_path)

# =========================
# 专栏：来自文件名
# =========================
def parse_columns_from_filename(doc_path):
    """
    例：
    第二期：会议报道；国际交流；会员动态；通知.docx
    """
    name = os.path.basename(doc_path)
    name = os.path.splitext(name)[0]

    if "：" not in name:
        return []

    _, cols = name.split("：", 1)
    return [c.strip() for c in cols.split("；") if c.strip()]

# =========================
# 主题：来自 Word 标题
# =========================
def is_topic_title(p):
    text = p.text.strip()
    style = p.style.name if p.style else ""

    return (
        style.startswith("Heading")
        or bool(re.match(r"（[一二三四五六七八九十]+）", text))
        or bool(re.match(r"\d+[\.\、]", text))
    )

def parse_topics(doc_path):
    doc = load_document(doc_path)
    topics = []

    for i, p in enumerate(doc.paragraphs):
        if is_topic_title(p):
            topics.append({
                "title": p.text.strip(),
                "index": i
            })

    return topics

# =========================
# 获取主题正文
# =========================
def get_topic_content(doc_path, topic_index):
    doc = load_document(doc_path)
    paragraphs = doc.paragraphs

    start = topic_index
    end = len(paragraphs)

    for i in range(start + 1, len(paragraphs)):
        if is_topic_title(paragraphs[i]):
            end = i
            break

    content = []
    for p in paragraphs[start + 1:end]:
        if p.text.strip():
            content.append(p.text.strip())

    return content

# =========================
# 表格（整篇提取）
# =========================
def extract_tables(doc_path):
    doc = load_document(doc_path)
    tables = []

    for idx, table in enumerate(doc.tables, start=1):
        rows = []
        for row in table.rows:
            rows.append([cell.text.strip() for cell in row.cells])
        tables.append({
            "index": idx,
            "rows": rows
        })

    return tables

# =========================
# 全文结构化搜索
# =========================
def structured_search(doc_path, keyword, context_window=2):
    if not keyword:
        return []

    doc = load_document(doc_path)
    results = []

    topics = parse_topics(doc_path)

    for i, p in enumerate(doc.paragraphs):
        if keyword not in p.text:
            continue

        current_topic = None
        for t in topics:
            if t["index"] <= i:
                current_topic = t
            else:
                break

        start = max(0, i - context_window)
        end = min(len(doc.paragraphs), i + context_window + 1)

        context = [
            doc.paragraphs[j].text.strip()
            for j in range(start, end)
            if doc.paragraphs[j].text.strip()
        ]

        results.append({
            "topic": current_topic["title"] if current_topic else None,
            "paragraph": p.text.strip(),
            "context": context,
            "topic_index": current_topic["index"] if current_topic else None
        })

    return results



