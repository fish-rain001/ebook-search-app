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

    issues = set()
    for f in os.listdir(year_dir):
        if f.endswith(".docx"):
            m = re.search(r"(第.+?期)", f)
            if m:
                issues.add(m.group(1))
    return sorted(list(issues))

def find_doc_path(year, issue):
    year_dir = os.path.join(BOOK_DIR, f"{year}年")
    files = glob.glob(os.path.join(year_dir, f"*{issue}*.docx"))
    return files[0] if files else None

# =========================
# Word 结构解析
# =========================
def load_document(doc_path):
    return Document(doc_path)

def is_column_title(p):
    """
    专栏标题：一、二、三……
    """
    return bool(re.match(r"[一二三四五六七八九十]+、", p.text.strip()))

def is_topic_title(p):
    """
    主题标题：（一）（二） 或 1. 2.
    """
    t = p.text.strip()
    return (
        bool(re.match(r"（[一二三四五六七八九十]+）", t)) or
        bool(re.match(r"\d+[\.\、]", t))
    )

# =========================
# 专栏 / 主题解析
# =========================
def parse_columns(doc_path):
    """
    返回：
    {
        "一、XXX": [paragraph_index, ...],
        ...
    }
    """
    doc = load_document(doc_path)
    columns = {}

    for i, p in enumerate(doc.paragraphs):
        if is_column_title(p):
            columns[p.text.strip()] = i

    return columns

def parse_topics(doc_path, column_title):
    """
    返回该专栏下的所有主题
    """
    doc = load_document(doc_path)
    columns = parse_columns(doc_path)

    if column_title not in columns:
        return []

    start = columns[column_title]
    next_columns = [
        idx for title, idx in columns.items()
        if idx > start
    ]
    end = min(next_columns) if next_columns else len(doc.paragraphs)

    topics = []
    for p in doc.paragraphs[start:end]:
        if is_topic_title(p):
            topics.append(p.text.strip())

    return topics

def get_topic_content(doc_path, column_title, topic_title):
    """
    返回某主题下的正文（含段落 + 表格）
    """
    doc = load_document(doc_path)
    columns = parse_columns(doc_path)

    start_col = columns[column_title]
    next_cols = [i for i in columns.values() if i > start_col]
    end_col = min(next_cols) if next_cols else len(doc.paragraphs)

    topic_start = None
    topic_end = end_col

    for i in range(start_col, end_col):
        p = doc.paragraphs[i]
        if p.text.strip() == topic_title:
            topic_start = i
        elif topic_start and is_topic_title(p):
            topic_end = i
            break

    if topic_start is None:
        return []

    content = []
    for p in doc.paragraphs[topic_start + 1: topic_end]:
        if p.text.strip():
            content.append(p.text)

    return content

# =========================
# 全文搜索
# =========================
def search_keyword(year, issue, keyword):
    doc_path = find_doc_path(year, issue)
    if not doc_path or not keyword:
        return []

    doc = load_document(doc_path)
    results = []

    for p in doc.paragraphs:
        if keyword in p.text:
            results.append(p.text.strip())

    return results
# =========================
# 表格解析
# =========================
def extract_tables(doc_path):
    """
    提取文档中所有表格
    返回：
    [
        {
            "index": 1,
            "rows": [
                ["单元格1", "单元格2", ...],
                ...
            ]
        },
        ...
    ]
    """
    doc = load_document(doc_path)
    tables_data = []

    for idx, table in enumerate(doc.tables, start=1):
        rows = []
        for row in table.rows:
            row_data = []
            for cell in row.cells:
                # 去掉多余换行
                text = cell.text.replace("\n", " ").strip()
                row_data.append(text)
            rows.append(row_data)

        tables_data.append({
            "index": idx,
            "rows": rows
        })

    return tables_data


def extract_tables_in_topic(doc_path, column_title, topic_title):
    """
    提取某一主题范围内出现的表格
    """
    doc = load_document(doc_path)

    columns = parse_columns(doc_path)
    if column_title not in columns:
        return []

    start_col = columns[column_title]
    next_cols = [i for i in columns.values() if i > start_col]
    end_col = min(next_cols) if next_cols else len(doc.paragraphs)

    topic_start = None
    topic_end = end_col

    for i in range(start_col, end_col):
        p = doc.paragraphs[i]
        if p.text.strip() == topic_title:
            topic_start = i
        elif topic_start and is_topic_title(p):
            topic_end = i
            break

    if topic_start is None:
        return []

    tables = []

    for table in doc.tables:
        # Word API 不直接告诉表格位置
        # 我们用表格前后文本近似判断
        table_text = " ".join(cell.text for row in table.rows for cell in row.cells)
        if table_text:
            tables.append(table)

    result = []
    for idx, table in enumerate(tables, start=1):
        rows = []
        for row in table.rows:
            rows.append([cell.text.strip() for cell in row.cells])
        result.append({
            "index": idx,
            "rows": rows
        })

    return result
# =========================
# 结构化搜索（带专栏 / 主题 / 上下文）
# =========================
def structured_search(doc_path, keyword, context_window=2):
    """
    返回：
    [
        {
            "column": "一、XXX",
            "topic": "（一）XXX",
            "paragraph": "命中段落",
            "context": ["前文", "命中", "后文"]
        },
        ...
    ]
    """
    if not keyword:
        return []

    doc = load_document(doc_path)
    columns = parse_columns(doc_path)

    # 构建段落 -> 专栏 / 主题映射
    para_map = []
    current_column = None
    current_topic = None

    for idx, p in enumerate(doc.paragraphs):
        text = p.text.strip()
        if not text:
            continue

        if is_column_title(p):
            current_column = text
            current_topic = None
        elif is_topic_title(p):
            current_topic = text

        para_map.append({
            "index": idx,
            "text": text,
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

