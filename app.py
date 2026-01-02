import streamlit as st
from logic import word_engine as we

st.set_page_config(
    page_title="电子书专栏检索系统",
    layout="wide"
)

st.title("📚 电子书专栏检索系统")

# =========================
# 左侧选择
# =========================
with st.sidebar:
    st.header("📂 文档选择")

    years = we.list_years()
    year = st.selectbox("年份", years)

    issues = we.list_issues(year)
    issue = st.selectbox("期刊", issues)

    doc_path = we.find_doc_path(year, issue)

# =========================
# 专栏 → 主题 → 正文
# =========================
columns = we.list_columns(doc_path)
column = st.selectbox("选择专栏（标题 1）", columns)

topics = we.list_topics(doc_path, column)
topic = st.selectbox("选择主题（标题 2）", topics)

st.markdown("---")
st.markdown(f"### {topic}")

content = we.get_topic_content(doc_path, column, topic)
for p in content:
    st.write(p)


