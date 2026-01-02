import streamlit as st
from logic import word_engine as we
from logic import ai_engine as ai
import os

st.set_page_config(page_title="电子书系统", layout="wide")
st.title("📚 电子书专栏 / 全文检索 / AI 分析系统")

# =========================
# 侧边栏：文档选择
# =========================
with st.sidebar:
    st.header("📂 文档选择")

    year = st.selectbox("年份", we.list_years())
    issue = st.selectbox("期刊", we.list_issues(year))

    doc_path = we.find_doc_path(year, issue)
    if not doc_path:
        st.error("未找到 Word 文件")
        st.stop()

# =========================
# Tabs
# =========================
tab_read, tab_search, tab_ai = st.tabs(
    ["📖 专栏阅读", "🔍 全文检索", "🤖 AI 分析"]
)

# ==================================================
# 📖 专栏 / 主题阅读（你原来的核心功能）
# ==================================================
with tab_read:
    st.subheader("📖 按专栏 / 主题阅读")

    columns = we.get_columns(doc_path)
    if not columns:
        st.warning("未识别到专栏（标题1）")
        st.stop()

    col1, col2 = st.columns([1, 2])

    with col1:
        column = st.selectbox("选择专栏", columns)

    topics = we.get_topics(doc_path, column)

    with col2:
        if topics:
            topic = st.selectbox("选择主题", topics)
        else:
            topic = None
            st.info("该专栏下没有主题")

    if topic:
        st.markdown("---")
        st.markdown(f"### {topic}")

        content = we.get_topic_content(doc_path, column, topic)

        if not content:
            st.info("该主题下无正文")
        else:
            for para in content:
                st.write(para)

# ==================================================
# 🔍 全文检索（Tkinter search_content 复刻）
# ==================================================
with tab_search:
    st.subheader("🔍 全文关键词搜索")

    keyword = st.text_input("关键词")

    if st.button("搜索"):
        result = we.full_text_search(doc_path, keyword)

        if not result:
            st.info("未找到结果")
        else:
            for r in result["contents"]:
                st.markdown(
                    f"**[{r['column']} → {r['topic']}]**"
                )
                st.write(r["content"])

# ==================================================
# 🤖 AI 分析
# ==================================================
with tab_ai:
    st.subheader("🤖 AI 分析")

    text = st.text_area("分析文本", height=260)
    question = st.text_input("问题")

    if st.button("开始分析"):
        with st.spinner("AI 分析中…"):
            answer = ai.ask_ai(question, text)
            st.write(answer)

