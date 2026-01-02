import streamlit as st
from logic import word_engine as we

st.set_page_config(layout="wide")
st.title("📚 电子书专栏检索系统")

# ========== 左侧 ==========
with st.sidebar:
    year = st.selectbox("年份", we.list_years())
    issue = st.selectbox("期刊", we.list_issues(year))
    doc_path = we.find_doc_path(year, issue)

# ========== 主界面 ==========
columns = we.list_columns(doc_path)
column = st.selectbox("专栏（标题1）", columns)

topics = we.list_topics(doc_path, column)
topic = st.selectbox("主题（标题2）", topics)

if st.button("📖 显示内容"):
    content = we.get_topic_content(doc_path, column, topic)
    for item in content:
        if isinstance(item, dict) and "table" in item:
            st.table(item["table"])
        else:
            st.write(item)


