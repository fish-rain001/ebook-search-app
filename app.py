import os
import re
import glob
import html
import threading
import streamlit as st

from logic import word_engine as we
from logic import ai_engine as ai


# ==================================================
# Session 初始化
# ==================================================
if "_jump_once" not in st.session_state:
    st.session_state._jump_once = False

for k in ["jump_year", "jump_issue", "jump_column", "jump_topic"]:
    if k not in st.session_state:
        st.session_state[k] = None


# ==================================================
# 页面配置
# ==================================================
st.set_page_config(page_title="电子书专栏检索系统", layout="wide")
st.title("📚 电子书专栏检索系统")


# ==================================================
# 高亮工具
# ==================================================
def highlight(text, kw):
    if not text or not kw:
        return html.escape(text)
    text = html.escape(text)
    return re.sub(
        re.escape(kw),
        lambda m: f"<mark style='background:#ffe066'>{m.group(0)}</mark>",
        text,
        flags=re.IGNORECASE
    )


# ==================================================
# Sidebar（跳转安全版）
# ==================================================
with st.sidebar:
    st.header("📂 文档选择")

    years = we.list_years()
    if not years:
        st.error("未检测到 data/电子书")
        st.stop()

    # ---------- 年份 ----------
    if st.session_state._jump_once and st.session_state.jump_year in years:
        year = st.session_state.jump_year
    else:
        year = years[0]

    year = st.selectbox("选择年份", years, index=years.index(year))

    # ---------- 期刊 ----------
    issues = we.list_issues(year)
    if not issues:
        st.warning("该年份无期刊")
        st.stop()

    if st.session_state._jump_once and st.session_state.jump_issue in issues:
        issue = st.session_state.jump_issue
    else:
        issue = issues[0]

    issue = st.selectbox("选择期刊", issues, index=issues.index(issue))

    doc_path = we.find_doc_path(year, issue)
    if not doc_path:
        st.error("未找到 Word")
        st.stop()

    # ⚠️ 只允许跳转使用一次
    if st.session_state._jump_once:
        st.session_state._jump_once = False


# ==================================================
# Tabs
# ==================================================
tab_read, tab_search, tab_ai = st.tabs(
    ["📖 专栏 / 主题阅读", "🔍 全文搜索", "🤖 AI 分析"]
)


# ==================================================
# 📖 阅读区（最终落点）
# ==================================================
with tab_read:
    st.subheader("📖 按专栏 / 主题阅读")

    columns = we.list_columns(doc_path)
    if not columns:
        st.warning("未识别到专栏")
        st.stop()

    column = (
        st.session_state.jump_column
        if st.session_state.jump_column in columns
        else columns[0]
    )

    c1, c2 = st.columns([1, 2])
    with c1:
        column = st.selectbox("选择专栏", columns, index=columns.index(column))

    topics = we.list_topics(doc_path, column)
    if not topics:
        st.info("该专栏无主题")
        st.stop()

    topic = (
        st.session_state.jump_topic
        if st.session_state.jump_topic in topics
        else topics[0]
    )

    with c2:
        topic = st.selectbox("选择主题", topics, index=topics.index(topic))

    st.markdown(f"### {topic}")

    content = we.get_topic_content(doc_path, column, topic)
    if not content:
        st.info("该主题无正文")
    else:
        for block in content:
            if isinstance(block, dict) and "table" in block:
                st.table(block["table"])
            else:
                st.write(block)


# ==================================================
# 🔍 搜索 + 跳转
# ==================================================
with tab_search:
    st.subheader("🔍 全文搜索")

    keyword = st.text_input("输入关键词")
    global_mode = st.checkbox("🌍 全局搜索（所有 Word）")

    if st.button("开始搜索"):
        if not keyword.strip():
            st.warning("请输入关键词")
            st.stop()

        results = []

        if global_mode:
            root = os.path.join("data", "电子书")
            files = glob.glob(os.path.join(root, "**", "*.docx"), recursive=True)
            for p in files:
                year = os.path.basename(os.path.dirname(p)).replace("年", "")
                for k, arr in we.full_text_search(p, keyword).items():
                    for r in arr:
                        r["year"] = year
                        r["issue"] = we.list_issues(year)[0]  # ✔ 保证合法
                        results.append(r)
        else:
            for k, arr in we.full_text_search(doc_path, keyword).items():
                for r in arr:
                    r["year"] = year
                    r["issue"] = issue
                    results.append(r)

        if not results:
            st.info("无匹配结果")
            st.stop()

        st.success(f"共找到 {len(results)} 条结果")

        for i, r in enumerate(results, 1):
            title = f"{r.get('column','')} → {r.get('topic','')}"
            with st.expander(f"{i}. {title}"):

                if "content" in r:
                    st.markdown(highlight(str(r["content"]), keyword), unsafe_allow_html=True)
                elif "hit" in r:
                    st.markdown(highlight(r["hit"], keyword), unsafe_allow_html=True)

                if st.button("📖 跳转阅读", key=f"jump_{i}"):
                    st.session_state.jump_year = r["year"]
                    st.session_state.jump_issue = r["issue"]
                    st.session_state.jump_column = r.get("column")
                    st.session_state.jump_topic = r.get("topic")
                    st.session_state._jump_once = True
                    st.experimental_rerun()


# ==================================================
# 🤖 AI
# ==================================================
with tab_ai:
    st.subheader("🤖 AI 学术辅助分析")

    text = "\n".join(t for t in content if isinstance(t, str))
    if st.button("开始分析"):
        placeholder = st.empty()

        def run_ai():
            placeholder.write(ai.analyze_topic(text))

        threading.Thread(target=run_ai).start()






