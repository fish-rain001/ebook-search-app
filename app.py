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
# 左侧：文档选择
# =========================
with st.sidebar:
    st.header("📂 文档选择")

    years = we.list_years()
    if not years:
        st.error("未检测到电子书数据，请检查 data/电子书 目录")
        st.stop()

    year = st.selectbox("选择年份", years)

    issues = we.list_issues(year)
    if not issues:
        st.warning("该年份下未找到期刊文件")
        st.stop()

    issue = st.selectbox("选择期刊", issues)

    doc_path = we.find_doc_path(year, issue)
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
# 📖 Tab 1：专栏 → 主题 → 正文 + 表格
# ==================================================
with tab_read:
    st.subheader("📖 按专栏 / 主题阅读")

    columns = we.parse_columns(doc_path)
    if not columns:
        st.info("该文档未识别到专栏结构")
    else:
        col_titles = list(columns.keys())

        # --- 支持搜索跳转 ---
        default_col = (
            col_titles.index(st.session_state["jump_column"])
            if "jump_column" in st.session_state
            and st.session_state["jump_column"] in col_titles
            else 0
        )

        col1, col2 = st.columns([1, 2])

        with col1:
            column_title = st.selectbox(
                "选择专栏",
                col_titles,
                index=default_col
            )

        topics = we.parse_topics(doc_path, column_title)

        with col2:
            if not topics:
                st.info("该专栏下未识别到主题")
                topic_title = None
            else:
                default_topic = (
                    topics.index(st.session_state["jump_topic"])
                    if "jump_topic" in st.session_state
                    and st.session_state["jump_topic"] in topics
                    else 0
                )

                topic_title = st.selectbox(
                    "选择主题",
                    topics,
                    index=default_topic
                )

        # --- 正文展示 ---
        if topic_title:
            st.markdown("---")
            st.markdown(f"### {topic_title}")

            content = we.get_topic_content(
                doc_path,
                column_title,
                topic_title
            )

            if not content:
                st.info("该主题下暂无正文内容")
            else:
                for para in content:
                    st.write(para)

            # =========================
            # 表格展示
            # =========================
            tables = we.extract_tables_in_topic(
                doc_path,
                column_title,
                topic_title
            )

            if tables:
                st.markdown("#### 📊 表格内容")
                for t in tables:
                    st.markdown(f"**表格 {t['index']}**")
                    st.table(t["rows"])

# ==================================================
# 🔍 Tab 2：全文搜索（结构化 + 跳转）
# ==================================================
with tab_search:
    st.subheader("🔍 全文关键词搜索（结构化）")

    keyword = st.text_input("输入关键词（支持定位到专栏 / 主题）")

    if st.button("开始搜索"):
        if not keyword.strip():
            st.warning("请输入关键词")
        else:
            results = we.structured_search(doc_path, keyword)

            if not results:
                st.info("未找到匹配内容")
            else:
                st.success(f"共找到 {len(results)} 条结果")

                for idx, r in enumerate(results, start=1):
                    with st.expander(
                        f"结果 {idx} ｜ {r['column']} → {r['topic']}"
                    ):
                        st.markdown("**命中段落：**")
                        st.write(r["paragraph"])

                        st.markdown("**上下文：**")
                        for line in r["context"]:
                            st.write(line)

                        if st.button(
                            "跳转到该主题",
                            key=f"jump_{idx}"
                        ):
                            st.session_state["jump_column"] = r["column"]
                            st.session_state["jump_topic"] = r["topic"]
                            st.experimental_rerun()

# ==================================================
# 🤖 Tab 3：AI 学术辅助分析
# ==================================================
with tab_ai:
    st.subheader("🤖 AI 学术辅助分析")

    st.info("AI 功能为辅助工具，结果仅供参考，不替代人工判断。")

    analysis_source = st.radio(
        "选择分析对象",
        ["当前主题正文", "自定义文本"]
    )

    if analysis_source == "当前主题正文":
        if "topic_title" not in locals() or not topic_title:
            st.warning("请先在【按结构阅读】中选择主题")
            st.stop()
        text = "\n".join(content)
    else:
        text = st.text_area(
            "请输入需要分析的文本",
            height=220
        )

    if st.button("开始 AI 分析"):
        if not text.strip():
            st.warning("分析内容不能为空")
        else:
            with st.spinner("AI 分析中，请稍候..."):
                try:
                    summary = ai.summarize_text(text)
                    keywords = ai.extract_keywords(text)
                    analysis = ai.analyze_topic(text)

                    st.markdown("### 📌 摘要")
                    st.write(summary)

                    st.markdown("### 🏷 关键词")
                    st.write(keywords)

                    st.markdown("### 🧠 学术分析")
                    st.write(analysis)

                except Exception as e:
                    st.error(f"AI 调用失败：{e}")
