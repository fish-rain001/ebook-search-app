import streamlit as st
from logic import word_engine as we
from logic import ai_engine as ai

# =========================
# 页面配置
# =========================
st.set_page_config(
    page_title="电子书专栏检索系统",
    layout="wide"
)

st.title("📚 电子书专栏检索系统（Web 版）")

# =========================
# Session State 初始化
# =========================
for key in [
    "year", "issue",
    "column_title", "topic_title",
    "content"
]:
    if key not in st.session_state:
        st.session_state[key] = None

# =========================
# 左侧：文档选择
# =========================
with st.sidebar:
    st.header("📂 文档选择")

    years = we.list_years()
    if not years:
        st.error("未检测到电子书数据，请检查 data/电子书 目录")
        st.stop()

    st.session_state.year = st.selectbox(
        "选择年份",
        years,
        index=years.index(st.session_state.year)
        if st.session_state.year in years else 0
    )

    issues = we.list_issues(st.session_state.year)
    if not issues:
        st.warning("该年份下未找到期刊文件")
        st.stop()

    st.session_state.issue = st.selectbox(
        "选择期刊",
        issues,
        index=issues.index(st.session_state.issue)
        if st.session_state.issue in issues else 0
    )

    doc_path = we.find_doc_path(
        st.session_state.year,
        st.session_state.issue
    )

    if not doc_path:
        st.error("未找到对应 Word 文件")
        st.stop()

# =========================
# 页面 Tabs
# =========================
tab_read, tab_search, tab_ai = st.tabs(
    ["📖 按结构阅读", "🔍 全文搜索", "🤖 AI 分析"]
)

# ==================================================
# 📖 Tab 1：结构阅读
# ==================================================
with tab_read:
    st.subheader("📖 按专栏 / 主题阅读")

    columns = we.parse_columns(doc_path)
    if not columns:
        st.info("该文档未识别到专栏结构")
        st.stop()

    col_titles = list(columns.keys())

    st.session_state.column_title = st.selectbox(
        "选择专栏",
        col_titles,
        index=col_titles.index(st.session_state.column_title)
        if st.session_state.column_title in col_titles else 0
    )

    topics = we.parse_topics(
        doc_path,
        st.session_state.column_title
    )

    if not topics:
        st.info("该专栏下未识别到主题")
        st.stop()

    st.session_state.topic_title = st.selectbox(
        "选择主题",
        topics,
        index=topics.index(st.session_state.topic_title)
        if st.session_state.topic_title in topics else 0
    )

    st.markdown("---")
    st.markdown(f"### {st.session_state.topic_title}")

    st.session_state.content = we.get_topic_content(
        doc_path,
        st.session_state.column_title,
        st.session_state.topic_title
    )

    if not st.session_state.content:
        st.info("该主题下暂无正文内容")
    else:
        for para in st.session_state.content:
            st.write(para)

    tables = we.extract_tables_in_topic(
        doc_path,
        st.session_state.column_title,
        st.session_state.topic_title
    )

    if tables:
        st.markdown("#### 📊 表格内容")
        for t in tables:
            st.markdown(f"**表格 {t['index']}**")
            st.table(t["rows"])

# ==================================================
# 🔍 Tab 2：全文搜索
# ==================================================
with tab_search:
    st.subheader("🔍 全文关键词搜索（结构化）")

    keyword = st.text_input("输入关键词")

    if st.button("开始搜索"):
        results = we.structured_search(doc_path, keyword)

        if not results:
            st.info("未找到匹配内容")
        else:
            for idx, r in enumerate(results, start=1):
                with st.expander(
                    f"结果 {idx} ｜ {r['column']} → {r['topic']}"
                ):
                    st.write(r["paragraph"])
                    for c in r["context"]:
                        st.write(c)

                    if st.button(
                        "跳转到该主题",
                        key=f"jump_{idx}"
                    ):
                        st.session_state.column_title = r["column"]
                        st.session_state.topic_title = r["topic"]
                        st.experimental_rerun()

# ==================================================
# 🤖 Tab 3：AI 分析
# ==================================================
with tab_ai:
    st.subheader("🤖 AI 学术辅助分析")

    if not st.session_state.content:
        st.warning("请先在【按结构阅读】中选择主题")
        st.stop()

    source = st.radio(
        "选择分析对象",
        ["当前主题正文", "自定义文本"]
    )

    if source == "当前主题正文":
        text = "\n".join(st.session_state.content)
    else:
        text = st.text_area("输入文本", height=220)

    if st.button("开始 AI 分析"):
        with st.spinner("AI 分析中..."):
            summary = ai.summarize_text(text)
            keywords = ai.extract_keywords(text)
            analysis = ai.analyze_topic(text)

            st.markdown("### 📌 摘要")
            st.write(summary)

            st.markdown("### 🏷 关键词")
            st.write(keywords)

            st.markdown("### 🧠 学术分析")
            st.write(analysis)

