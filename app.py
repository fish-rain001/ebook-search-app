import streamlit as st
import html

from logic import word_engine as we
from logic import ai_engine as ai


# =========================
# 页面配置
# =========================
st.set_page_config(page_title="电子书检索系统", layout="wide")

st.title("📚 电子书检索与 AI 分析系统")


# =========================
# Session 初始化
# =========================
for k in [
    "year", "issue", "column", "topic",
    "topic_content",
    "ai_question", "ai_result"
]:
    if k not in st.session_state:
        st.session_state[k] = None


# =========================
# 左侧：目录选择
# =========================
with st.sidebar:
    st.header("📂 目录选择")

    years = we.list_years()
    year = st.selectbox("年份", years, index=0 if years else None)

    if year:
        issues = we.list_issues(year)
        issue = st.selectbox("期刊", issues)

        doc_path = we.find_doc_path(year, issue)

        if doc_path:
            columns = we.list_columns(doc_path)
            column = st.selectbox("专栏", columns)

            if column:
                topics = we.list_topics(doc_path, column)
                topic = st.selectbox("主题", topics)

                if topic:
                    st.session_state.year = year
                    st.session_state.issue = issue
                    st.session_state.column = column
                    st.session_state.topic = topic


# =========================
# 主区：主题阅读
# =========================
if st.session_state.topic:
    st.subheader(
        f"📖 {st.session_state.year}年 / {st.session_state.issue} / "
        f"{st.session_state.column} / {st.session_state.topic}"
    )

    doc_path = we.find_doc_path(
        st.session_state.year,
        st.session_state.issue
    )

    content = we.get_topic_content(
        doc_path,
        st.session_state.column,
        st.session_state.topic
    )

    st.session_state.topic_content = content

    # -------- 正文展示 --------
    for item in content:
        if isinstance(item, str):
            st.markdown(f"<p>{html.escape(item)}</p>", unsafe_allow_html=True)

        elif isinstance(item, dict) and "table" in item:
            st.table(item["table"])


# =========================
# 工具：内容转纯文本
# =========================
def topic_content_to_text(content):
    texts = []
    for item in content:
        if isinstance(item, str):
            texts.append(item)
        elif isinstance(item, dict) and "table" in item:
            for row in item["table"]:
                texts.append(" | ".join(row))
    return "\n".join(texts)


# =========================
# 🧠 AI 分析区（重点）
# =========================
if st.session_state.topic_content:
    st.divider()
    st.subheader("🧠 AI 分析（基于当前主题内容）")

    question = st.text_input(
        "请输入你要让 AI 分析的问题",
        value=st.session_state.ai_question or "",
        placeholder="例如：这篇文章的核心观点是什么？"
    )

    if st.button("🚀 AI 分析"):
        if not question.strip():
            st.warning("请输入问题")
        else:
            with st.spinner("AI 正在分析，请稍候..."):
                context = topic_content_to_text(
                    st.session_state.topic_content
                )
                try:
                    result = ai.ask_ai(question, context)
                    st.session_state.ai_question = question
                    st.session_state.ai_result = result
                except Exception as e:
                    st.error(str(e))

    if st.session_state.ai_result:
        st.markdown("### 📊 AI 分析结果")
        st.markdown(st.session_state.ai_result)
