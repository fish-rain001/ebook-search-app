import streamlit as st
from logic import word_engine as we
from logic import ai_engine as ai
import os

# =========================
# 页面配置
# =========================
st.set_page_config(
    page_title="电子书系统",
    layout="wide"
)

st.title("📚 电子书专栏 / 全文检索 / AI 分析系统")

# =========================
# 左侧：文档选择
# =========================
with st.sidebar:
    st.header("📂 文档选择")

    years = we.list_years()
    if not years:
        st.error("未检测到 data/电子书 目录")
        st.stop()

    year = st.selectbox("选择年份", years)

    issues = we.list_issues(year)
    if not issues:
        st.warning("该年份下没有期刊")
        st.stop()

    issue = st.selectbox("选择期刊", issues)

    doc_path = we.find_doc_path(year, issue)
    if not doc_path or not os.path.exists(doc_path):
        st.error("未找到 Word 文件")
        st.stop()

    st.success(os.path.basename(doc_path))

# =========================
# Tabs
# =========================
tab_read, tab_search, tab_ai = st.tabs(
    ["📖 专栏阅读", "🔍 全文检索", "🤖 AI 分析"]
)

# ==================================================
# 📖 专栏 / 主题阅读（严格按你原始逻辑）
# ==================================================
with tab_read:
    st.subheader("📖 按专栏 / 主题阅读")

    columns_dict = we.parse_columns(doc_path)

    if not columns_dict:
        st.warning("未识别到专栏结构")
        st.stop()

    column_titles = list(columns_dict.keys())

    col1, col2 = st.columns([1, 2])

    with col1:
        column_title = st.selectbox("选择专栏", column_titles)

    topics = we.parse_topics(doc_path, column_title)

    with col2:
        if topics:
            topic_title = st.selectbox("选择主题", topics)
        else:
            topic_title = None
            st.info("该专栏下没有主题")

    if topic_title:
        st.markdown("---")
        st.markdown(f"### {topic_title}")

        content = we.get_topic_content(
            doc_path,
            column_title,
            topic_title
        )

        if not content:
            st.info("该主题下没有正文内容")
        else:
            for para in content:
                st.write(para)

# ==================================================
# 🔍 全文检索（你 Tkinter 的 search_content）
# ==================================================
with tab_search:
    st.subheader("🔍 全文关键词搜索")

    keyword = st.text_input("请输入关键词")

    if st.button("开始搜索"):
        if not keyword.strip():
            st.warning("请输入关键词")
        else:
            result = we.search_keyword(year, issue, keyword)

            if not result:
                st.info("未找到匹配内容")
            else:
                st.success(f"找到 {len(result)} 条结果")
                for r in result:
                    st.write(r)

# ==================================================
# 🤖 AI 分析
# ==================================================
with tab_ai:
    st.subheader("🤖 AI 学术辅助分析")

    text = st.text_area("分析文本", height=260)
    question = st.text_input("分析问题")

    if st.button("开始 AI 分析"):
        if not text.strip():
            st.warning("请输入分析文本")
        elif not question.strip():
            st.warning("请输入问题")
        else:
            with st.spinner("AI 分析中…"):
                answer = ai.ask_ai(question, text)
                st.markdown("### 💡 AI 分析结果")
                st.write(answer)
)

