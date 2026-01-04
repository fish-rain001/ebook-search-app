import os
import glob
import re
import html
import threading
import streamlit as st

from logic import word_engine as we
from logic import ai_engine as ai


# ==================================================
# Session 初始化（非常重要）
# ==================================================
for k in [
    "jump_year", "jump_issue",
    "jump_column", "jump_topic",
    "force_read"
]:
    if k not in st.session_state:
        st.session_state[k] = None


# ==================================================
# 页面配置
# ==================================================
st.set_page_config(
    page_title="电子书专栏检索系统",
    layout="wide"
)

st.title("📚 电子书专栏检索系统")


# ==================================================
# 工具：高亮
# ==================================================
def highlight(text, keyword):
    if not text or not keyword:
        return html.escape(text)
    text = html.escape(text)
    return re.sub(
        re.escape(keyword),
        lambda m: f"<mark style='background:#ffe066'>{m.group(0)}</mark>",
        text,
        flags=re.IGNORECASE
    )


# ==================================================
# 搜索缓存
# ==================================================
@st.cache_data(show_spinner=False)
def cached_search(doc_path, keyword):
    return we.full_text_search(doc_path, keyword)


@st.cache_data(show_spinner=False)
def cached_global_search(all_docs, keyword):
    result = {"topics": [], "contents": [], "tables": []}
    for p in all_docs:
        try:
            r = we.full_text_search(p, keyword)
            year = os.path.basename(os.path.dirname(p))
            issue = os.path.basename(p)
            for k in result:
                for x in r[k]:
                    x["year"] = year
                    x["issue"] = issue
                    result[k].append(x)
        except Exception:
            pass
    return result


# ==================================================
# Sidebar：文档选择（完全支持跳转）
# ==================================================
with st.sidebar:
    st.header("📂 文档选择")

    years = we.list_years()
    if not years:
        st.error("未检测到 data/电子书")
        st.stop()

    year = (
        st.session_state.jump_year
        if st.session_state.jump_year in years
        else years[0]
    )
    year = st.selectbox("选择年份", years, index=years.index(year))

    issues = we.list_issues(year)
    if not issues:
        st.warning("该年份无期刊")
        st.stop()

    issue = (
        st.session_state.jump_issue
        if st.session_state.jump_issue in issues
        else issues[0]
    )
    issue = st.selectbox("选择期刊", issues, index=issues.index(issue))

    doc_path = we.find_doc_path(year, issue)
    if not doc_path:
        st.error("未找到 Word")
        st.stop()


# ==================================================
# Tabs
# ==================================================
tab_read, tab_search, tab_ai = st.tabs(
    ["📖 专栏 / 主题阅读", "🔍 全文搜索", "🤖 AI 分析"]
)


# ==================================================
# 📖 阅读（跳转最终落点）
# ==================================================
with tab_read:
    st.subheader("📖 按专栏 / 主题阅读")

    if st.session_state.force_read:
        st.success("📌 已跳转到搜索命中的位置")
        st.session_state.force_read = False

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
# 🔍 搜索（带高亮 + 跳转）
# ==================================================
with tab_search:
    st.subheader("🔍 全文搜索")

    keyword = st.text_input("输入关键词")
    global_mode = st.checkbox("🌍 全局搜索（所有 Word）")

    if st.button("开始搜索"):
        if not keyword.strip():
            st.warning("请输入关键词")
            st.stop()

        if global_mode:
            root = os.path.join("data", "电子书")
            docs = glob.glob(os.path.join(root, "**", "*.docx"), recursive=True)
            with st.spinner(f"正在搜索 {len(docs)} 个文档"):
                results = cached_global_search(docs, keyword)
        else:
            results = cached_search(doc_path, keyword)

        total = sum(len(results[k]) for k in results)
        if total == 0:
            st.info("无匹配结果")
            st.stop()

        st.success(f"共找到 {total} 条结果")
        idx = 1

        for group in ["topics", "contents", "tables"]:
            for r in results[group]:
                title = f"[{r.get('year','')}] {r.get('issue','')} ｜ {r.get('column','')} → {r.get('topic','')}"
                with st.expander(f"{idx}. {title}"):

                    if group == "topics":
                        st.markdown(highlight(r["hit"], keyword), unsafe_allow_html=True)
                    elif group == "contents":
                        st.markdown(highlight(r["content"], keyword), unsafe_allow_html=True)
                    else:
                        for row in r["content"]:
                            st.markdown(
                                " | ".join(highlight(c, keyword) for c in row),
                                unsafe_allow_html=True
                            )

                    if st.button("📖 跳转阅读", key=f"jump_{idx}"):
                        st.session_state.jump_year = r.get("year")
                        st.session_state.jump_issue = r.get("issue")
                        st.session_state.jump_column = r.get("column")
                        st.session_state.jump_topic = r.get("topic")
                        st.session_state.force_read = True
                        st.experimental_rerun()

                idx += 1


# ==================================================
# 🤖 AI 分析
# ==================================================
with tab_ai:
    st.subheader("🤖 AI 学术辅助")

    source = st.radio("分析对象", ["当前主题", "自定义文本"])

    if source == "当前主题":
        text = "\n".join(t for t in content if isinstance(t, str))
    else:
        text = st.text_area("输入文本", height=260)

    if st.button("开始分析"):
        placeholder = st.empty()

        def run_ai():
            try:
                placeholder.markdown("### 📌 摘要")
                placeholder.write(ai.summarize_text(text))
                placeholder.markdown("### 🏷 关键词")
                placeholder.write(ai.extract_keywords(text))
                placeholder.markdown("### 🧠 分析")
                placeholder.write(ai.analyze_topic(text))
            except Exception as e:
                placeholder.error(str(e))

        threading.Thread(target=run_ai).start()





