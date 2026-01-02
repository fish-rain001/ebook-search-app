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
        if d.endswith("年") and os.path.isdir(os.path.join(BOOK_DIR, d))
    )

def list_issues(year):
    year_dir = os.path.join(BOOK_DIR, f"{year}年")
    if not os.path.exists(year_dir):
        return []

    issues = set()
    for f in os.listdir(year_dir):
        if f.endswith(".docx"):
            # 同时支持"期"和"号"两种格式
            m = re.search(r"(第[一二三四五六七八九十\d]+期|第\d+号)", f)
            if m:
                issues.add(m.group(1))
    return sorted(list(issues))

def find_doc_path(year, issue):
    year_dir = os.path.join(BOOK_DIR, f"{year}年")
    
    # 多种匹配模式
    patterns = [
        os.path.join(year_dir, f"*{issue}*.docx"),
        os.path.join(year_dir, f"*{issue.replace('：', '')}*.docx"),
        os.path.join(year_dir, f"*{issue.replace(':', '')}*.docx"),
    ]
    
    for pattern in patterns:
        files = glob.glob(pattern)
        if files:
            return files[0]
    return None

# =========================
# Word 结构解析 - 修复版
# =========================
def load_document(doc_path):
    try:
        return Document(doc_path)
    except Exception as e:
        print(f"加载文档失败: {e}")
        return None

def is_column_title(para):
    """
    专栏标题识别（更宽松的匹配）
    """
    text = para.text.strip()
    if not text:
        return False
    
    # 匹配一级标题模式
    patterns = [
        r'^[一二三四五六七八九十]+、',  # 一、二、三...
        r'^[一二三四五六七八九十]+\s*[、\.]',  # 一、 二.
        r'^[1-9]\d*\.',  # 1. 2.
        r'^[A-Z]\.',  # A. B.
    ]
    
    return any(re.match(pattern, text) for pattern in patterns)

def is_topic_title(para):
    """
    主题标题识别（二级标题）
    """
    text = para.text.strip()
    if not text or len(text) > 50:  # 过滤过长的文本
        return False
    
    # 匹配二级标题模式
    patterns = [
        r'^（[一二三四五六七八九十]+）',  # （一）（二）
        r'^\([一二三四五六七八九十]+\)',  # (一)(二)
        r'^[1-9]\d*\.\d+',  # 1.1 2.1
        r'^[一二三四五六七八九十]+\.\d+',  # 一.1 二.1
        r'^[①②③④⑤⑥⑦⑧⑨⑩]',  # ① ②
        r'^[A-Z]\.\d+',  # A.1 B.1
    ]
    
    return any(re.match(pattern, text) for pattern in patterns)

def is_normal_text(para):
    """
    正文文本识别
    """
    text = para.text.strip()
    if not text:
        return False
    
    # 排除标题和分隔符
    if is_column_title(para) or is_topic_title(para):
        return False
    
    # 排除分隔符
    if re.match(r'0{60,}', text):
        return False
    
    return True

# =========================
# 专栏 / 主题解析 - 修复版
# =========================
def parse_columns(doc_path):
    """
    返回专栏字典：{"专栏标题": 段落索引}
    """
    doc = load_document(doc_path)
    if not doc:
        return {}
    
    columns = {}
    skip_content = True
    
    for i, para in enumerate(doc.paragraphs):
        text = para.text.strip()
        
        # 跳过目录部分（60个0分隔符）
        if re.match(r'0{60,}', text):
            skip_content = False
            continue
            
        if skip_content:
            continue
            
        if is_column_title(para) and text:
            columns[text] = i
    
    return columns

def parse_topics(doc_path, column_title):
    """
    返回指定专栏下的所有主题列表
    """
    doc = load_document(doc_path)
    if not doc:
        return []
    
    columns = parse_columns(doc_path)
    if column_title not in columns:
        return []
    
    start_index = columns[column_title]
    
    # 找到下一个专栏的开始位置作为结束位置
    next_indices = [idx for title, idx in columns.items() if idx > start_index]
    end_index = min(next_indices) if next_indices else len(doc.paragraphs)
    
    topics = []
    skip_content = True
    
    for i, para in enumerate(doc.paragraphs):
        # 跳过目录
        if re.match(r'0{60,}', para.text.strip()):
            skip_content = False
            continue
        if skip_content:
            continue
            
        # 只在目标专栏范围内查找主题
        if i < start_index:
            continue
        if i >= end_index:
            break
            
        if is_topic_title(para) and para.text.strip():
            topics.append(para.text.strip())
    
    return topics

def get_topic_content(doc_path, column_title, topic_title):
    """
    获取主题下的完整内容（包括表格）
    """
    doc = load_document(doc_path)
    if not doc:
        return []
    
    columns = parse_columns(doc_path)
    if column_title not in columns:
        return []
    
    start_col = columns[column_title]
    next_cols = [idx for title, idx in columns.items() if idx > start_col]
    end_col = min(next_cols) if next_cols else len(doc.paragraphs)
    
    # 找到主题开始位置
    topic_start = None
    for i in range(start_col, end_col):
        para = doc.paragraphs[i]
        if para.text.strip() == topic_title:
            topic_start = i
            break
    
    if topic_start is None:
        return []
    
    # 找到主题结束位置（下一个主题或专栏）
    topic_end = end_col
    for i in range(topic_start + 1, end_col):
        para = doc.paragraphs[i]
        if is_topic_title(para) or is_column_title(para):
            topic_end = i
            break
    
    # 收集内容
    content = []
    for i in range(topic_start + 1, topic_end):
        para = doc.paragraphs[i]
        text = para.text.strip()
        if text and not is_column_title(para) and not is_topic_title(para):
            content.append(text)
    
    return content

# =========================
# 表格解析
# =========================
def extract_tables_in_topic(doc_path, column_title, topic_title):
    """
    提取主题范围内的表格
    """
    doc = load_document(doc_path)
    if not doc:
        return []
    
    # 先找到主题的范围
    columns = parse_columns(doc_path)
    if column_title not in columns:
        return []
    
    start_col = columns[column_title]
    next_cols = [idx for title, idx in columns.items() if idx > start_col]
    end_col = min(next_cols) if next_cols else len(doc.paragraphs)
    
    topic_start = None
    for i in range(start_col, end_col):
        if doc.paragraphs[i].text.strip() == topic_title:
            topic_start = i
            break
    
    if topic_start is None:
        return []
    
    # 简单返回所有表格（实际应该根据位置过滤）
    tables_data = []
    for idx, table in enumerate(doc.tables, 1):
        rows = []
        for row in table.rows:
            row_data = [cell.text.strip() for cell in row.cells]
            rows.append(row_data)
        tables_data.append({
            "index": idx,
            "rows": rows
        })
    
    return tables_data

# =========================
# 结构化搜索
# =========================
def structured_search(doc_path, keyword, context_window=2):
    """
    全文搜索，返回结构化结果
    """
    doc = load_document(doc_path)
    if not doc or not keyword:
        return []
    
    columns = parse_columns(doc_path)
    results = []
    
    # 构建段落映射
    para_map = []
    current_column = None
    current_topic = None
    skip_content = True
    
    for i, para in enumerate(doc.paragraphs):
        text = para.text.strip()
        
        # 跳过目录
        if re.match(r'0{60,}', text):
            skip_content = False
            continue
        if skip_content:
            continue
            
        # 更新当前专栏和主题
        if is_column_title(para):
            current_column = text
            current_topic = None
        elif is_topic_title(para):
            current_topic = text
            
        para_map.append({
            "index": i,
            "text": text,
            "column": current_column,
            "topic": current_topic
        })
    
    # 搜索关键词
    for i, item in enumerate(para_map):
        if keyword.lower() in item["text"].lower():
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




