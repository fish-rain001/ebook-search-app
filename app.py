import streamlit as st
from logic import word_engine as we

st.set_page_config(
    page_title="电子书专栏检索系统",
    layout="wide"
)

st.title("📚 电子书专栏检索系统")

# =========================
# Session State
# =========================
for k in ["year", "issue", "topic"]:
    if k not in st.session_state:
        st.session_state[k] = None

# =========================
# 左侧：文档选择
# =========================
with st.sidebar:
    st.header("📂 文档选择")

    years = we.list_years()
    st.session_state.year = st.selectbox("年份", years)

    issues = we.list_issues(st.session_state.year)
    st.session_state.issue = st.selectbox("期刊", issues)

    doc_path = we.find_doc_path(
        st.session_state.year,
        st.session_state.issue
    )

# =========================
# 专栏（来自文件名）
# =========================
columns = we.parse_columns_from_filename(doc_path)
st.markdown("### 🗂 专栏")
st.write(" / ".join(columns))

# =========================
# Tabs
# =========================
tab_read, tab_search = st.tabs(["📖 阅读", "🔍 搜索"])

# =========================
# 阅读
# =========================
with tab_read:
    topics = we.parse_topics(doc_path)
    titles = [t["title"] for t in topics]

    topic_title = st.selectbox("选择主题", titles)
    topic = next(t for t in topics if t["title"] == topic_title)

    content = we.get_topic_content(doc_path, topic["index"])

    st.markdown("---")
    for p in content:
        st.write(p)

# =========================
# 搜索
# =========================
with tab_search:
    keyword = st.text_input("关键词")

    if st.button("搜索"):
        results = we.structured_search(doc_path, keyword)

        for r in results:
            with st.expander(f"{r['topic']}"):
                st.write(r["paragraph"])
                for c in r["context"]:
                    st.write(c)


