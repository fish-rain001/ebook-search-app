import os
import glob
import re
import html
import threading
import streamlit as st

from logic import word_engine as we
from logic import ai_engine as ai


# ==================================================
# Session 初始化（关键）
# ==================================================
for k in [
    "jump_year", "jump_issue",
    "jump_column", "jump_topic",
    "active_tab"
]:
    if k not in st.session_state:
        st.session_state[k] = None

if st.session_state.active_tab is None:
    st.session_state.active_tab = "🔍 全文搜索"


# ==================================================
# 页面配置
# ==================================================
st.set_page_config(
    page_title="电子书专栏检索系统",
    layout="wide"
)

st.title("📚 电子书专栏检索系统")


# ==================================================
# 工具：高亮
# ==================================================
def highlight(text, keyword):
    if not text or not keyword:
        return html.escape(text)
    text = html.escape(text)
    return re.sub(
        re.escape(keyword),
        lambda m: f"<mark style='background:#ffe066'>{m.group(0)}</mark>",
        text,
        flags=re.IGNORECASE
    )


# ==================================================
# 搜索缓存
# ==================================================
@st.cache_data(show_spinner=False)
def cached_search(doc_path, keyword):
    return we.full_text_search(doc_path, keyword)


@st.cache_data(show_spinner=False)
def cached_global_search(all_docs, keyword):
    result = {"topics": [], "contents": [], "tables": []}
    for p in all_docs:
        try:
            r = we.full_text_search(p, keyword)
            year = os.path.basename(os.path.dirname(p))
            issue = os.path.basename(p)
            for k in result:
                for x in r[k]:
                    x["year"] = year
                    x["issue"] = issue
                    result[k].append(x)
        except Exception:
            pass
    return result


# ==================================================
# Sidebar：文档选择（支持跳转）
# ==================================================
with st.sidebar:
    st.header("📂 文档选择")

    years = we.list_years()
    if not years:
        st.error("未检测到 data/电子书")
        st.stop()

    year = st.session_state.jump_year if st.session_state.jump_year in years else years[0]
    year = st.selectbox("选择年份", years, index=years.index(year))

    issues = we.list_issues(year)
    if not issues:
        st.warning("该年份无期刊")
        st.stop()

    issue = st.session_state.jump_issue if st.session_state.jump_issue in issues else issues[0]
    issue = st.selectbox("选择期刊", issues, index=issues.index(issue))

    doc_path = we.find_doc_path(year, issue)
    if not doc_path:
        st.error("未找到 Word")
        st.stop()


# ==================================================
# ✅ 可控 Tab（最终正确方案）
# ==================================================
tab = st.radio(
    "功能区",
    ["📖 专栏 / 主题阅读", "🔍 全文搜索", "🤖 AI 分析"],
    horizontal=True,
    key="active_tab"
)


# ==================================================
# 📖 阅读区
# ==================================================
if tab == "📖 专栏 / 主题阅读":
    st.subheader("📖 按专栏 / 主题阅读")

    columns = we.list_columns(doc_path)
    if not columns:
        st.warning("未识别到专栏")
        st.stop()

    column = st.session_state.jump_column if st.session_state.jump_column in columns else columns[0]

    c1, c2 = st.columns([1, 2])
    with c1:
        column = st.selectbox("选择专栏", columns, index=columns.index(column))

    topics = we.list_topics(doc_path, column)
    if not topics:
        st.info("该专栏无主题")
        st.stop()

    topic = st.session_state.jump_topic if st.session_state.jump_topic in topics else topics[0]

    with c2:
        topic = st.selectbox("选择主题", topics, index=topics.index(topic))

    st.markdown(f"### {topic}")

    content = we.get_topic_content(doc_path, column, topic)
    for block in content:
        if isinstance(block, dict) and "table" in block:
            st.table(block["table"])
        else:
            st.write(block)


# ==================================================
# 🔍 搜索区（跳转核心）
# ==================================================
if tab == "🔍 全文搜索":
    st.subheader("🔍 全文搜索")

    keyword = st.text_input("输入关键词")
    global_mode = st.checkbox("🌍 全局搜索（所有 Word）")

    if st.button("开始搜索"):
        if global_mode:
            root = os.path.join("data", "电子书")
            docs = glob.glob(os.path.join(root, "**", "*.docx"), recursive=True)
            results = cached_global_search(docs, keyword)
        else:
            results = cached_search(doc_path, keyword)

        idx = 1
        for group in ["topics", "contents", "tables"]:
            for r in results[group]:
                with st.expander(f"{idx}. {r.get('column','')} → {r.get('topic','')}"):
                    if group == "contents":
                        st.markdown(highlight(r["content"], keyword), unsafe_allow_html=True)

                    if st.button("📖 跳转阅读", key=f"jump_{idx}"):
                        st.session_state.jump_year = r.get("year")
                        st.session_state.jump_issue = r.get("issue")
                        st.session_state.jump_column = r.get("column")
                        st.session_state.jump_topic = r.get("topic")
                        st.session_state.active_tab = "📖 专栏 / 主题阅读"
                        st.experimental_rerun()
                idx += 1


# ==================================================
# 🤖 AI 分析
# ==================================================
if tab == "🤖 AI 分析":
    st.subheader("🤖 AI 学术辅助")

    text = st.text_area("输入文本", height=260)
    if st.button("开始分析"):
        placeholder = st.empty()

        def run_ai():
            placeholder.write(ai.summarize_text(text))
            placeholder.write(ai.extract_keywords(text))
            placeholder.write(ai.analyze_topic(text))

        threading.Thread(target=run_ai).start()
