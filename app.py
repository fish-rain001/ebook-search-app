import os
import re
import glob
import html
import threading
import streamlit as st

from logic import word_engine as we
from logic import ai_engine as ai


# ==================================================
# 页面配置
# ==================================================
st.set_page_config(page_title="电子书专栏检索系统", layout="wide")
st.title("📚 电子书专栏检索系统（Streamlit）")


# ==================================================
# Session 初始化
# ==================================================
if "jump_target" not in st.session_state:
    st.session_state.jump_target = None

if "search_cache" not in st.session_state:
    st.session_state.search_cache = {}


# ==================================================
# 高亮函数
# ==================================================
def highlight(text, kw):
    if not text or not kw:
        return text
    safe = html.escape(text)
    return re.sub(
        re.escape(kw),
        lambda m: f"<mark style='background:#ffe066'>{m.group(0)}</mark>",
        safe,
        flags=re.IGNORECASE
    )


# ==================================================
# Sidebar：文档选择（完全保留你原逻辑）
# ==================================================
with st.sidebar:
    st.header("📂 文档选择")

    years = we.list_years()
    if not years:
        st.error("未检测到 data/电子书")
        st.stop()

    year = st.selectbox("选择年份", years)
    issues = we.list_issues(year)
    issue = st.selectbox("选择期刊", issues)

    doc_path = we.find_doc_path(year, issue)
    if not doc_path:
        st.stop()


# ==================================================
# Tabs
# ==================================================
tab_read, tab_search, tab_ai = st.tabs(
    ["📖 专栏 / 主题阅读", "🔍 全文搜索", "🤖 AI 分析"]
)


# ==================================================
# 📖 阅读区（完全沿用你原逻辑）
# ==================================================
with tab_read:
    st.subheader("📖 按专栏 / 主题阅读")

    columns = we.list_columns(doc_path)
    if not columns:
        st.info("未识别到专栏")
        st.stop()

    column = st.selectbox("选择专栏", columns)
    topics = we.list_topics(doc_path, column)

    if not topics:
        st.info("该专栏无主题")
        st.stop()

    topic = st.selectbox("选择主题", topics)

    st.markdown(f"### {topic}")
    content = we.get_topic_content(doc_path, column, topic)

    for block in content:
        if isinstance(block, dict) and "table" in block:
            st.table(block["table"])
        else:
            st.write(block)


# ==================================================
# 🔍 搜索（在你原版基础上增强）
# ==================================================
with tab_search:
    st.subheader("🔍 全文搜索")

    keyword = st.text_input("输入关键词")
    global_mode = st.checkbox("🌍 全局搜索（所有 Word）")

    if st.button("开始搜索"):
        if not keyword.strip():
            st.warning("请输入关键词")
            st.stop()

        cache_key = f"{keyword}_{global_mode}_{year}_{issue}"
        if cache_key in st.session_state.search_cache:
            results = st.session_state.search_cache[cache_key]
        else:
            results = []

            if global_mode:
                root = os.path.join("data", "电子书")
                files = glob.glob(os.path.join(root, "**", "*.docx"), recursive=True)

                for p in files:
                    res = we.full_text_search(p, keyword)
                    for group in res.values():
                        for r in group:
                            r["_doc_path"] = p
                            results.append(r)
            else:
                res = we.full_text_search(doc_path, keyword)
                for group in res.values():
                    results.extend(group)

            st.session_state.search_cache[cache_key] = results

        if not results:
            st.info("未找到匹配内容")
            st.stop()

        st.success(f"共找到 {len(results)} 条结果")

        for i, r in enumerate(results, 1):
            title = f"{r.get('column','')} → {r.get('topic','')}"
            with st.expander(f"{i}. {title}"):

                if "content" in r:
                    st.markdown(
                        highlight(str(r["content"]), keyword),
                        unsafe_allow_html=True
                    )
                elif "hit" in r:
                    st.markdown(
                        highlight(r["hit"], keyword),
                        unsafe_allow_html=True
                    )

                if st.button("📖 跳转阅读", key=f"jump_{i}"):
                    st.session_state.jump_target = r
                    st.experimental_rerun()


# ==================================================
# 🤖 AI（不动你原结构）
# ==================================================
with tab_ai:
    st.subheader("🤖 AI 学术辅助分析")

    text = "\n".join(t for t in content if isinstance(t, str))
    if st.button("开始 AI 分析"):
        placeholder = st.empty()

        def run_ai():
            placeholder.write(ai.analyze_topic(text))

        threading.Thread(target=run_ai).start()







