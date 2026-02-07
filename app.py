import os
import glob
import re
import html
import streamlit as st

from logic import word_engine as we
from logic import ai_engine as ai


# ==================================================
# 页面配置
# ==================================================
st.set_page_config(
    page_title="档案资料管理系统",
    layout="wide"
)

st.title("📚 档案资料管理系统")


# ==================================================
# 高亮工具
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
# Sidebar：文档选择
# ==================================================
collections = we.list_collections()

if not collections:
    st.error("未检测到任何资料库")
    st.stop()

collection = st.selectbox("选择资料", collections)

with st.sidebar:
    st.header("📂 文档选择")

    years = we.list_years(collection)

    if not years:
        st.error("未检测到年份")
        st.stop()

    year = st.selectbox("选择年份", years)

    issues = we.list_issues(collection, year)

    if not issues:
        st.warning("该年份无期刊")
        st.stop()

    issue = st.selectbox("选择期刊", issues)

    doc_path = we.find_doc_path(collection, year, issue)

    if not doc_path:
        st.error("未找到 Word")
        st.stop()


# ==================================================
# 功能区
# ==================================================
tab = st.radio(
    "功能区",
    ["📖 专栏 / 主题阅读", "🔍 全文搜索"],
    horizontal=True
)


# ==================================================
# 📖 阅读区
# ==================================================
if tab == "📖 专栏 / 主题阅读":

    st.subheader("📖 按专栏 / 主题阅读")

    columns = we.list_columns(doc_path)
    if not columns:
        st.warning("未识别到专栏")
        st.stop()

    c1, c2 = st.columns([1, 2])

    with c1:
        column = st.selectbox("选择专栏", columns)

    topics = we.list_topics(doc_path, column)
    if not topics:
        st.info("该专栏无主题")
        st.stop()

    with c2:
        topic = st.selectbox("选择主题", topics)

    st.markdown(f"### {topic}")

    content = we.get_topic_content(doc_path, column, topic)

    if not content:
        st.info("该主题无正文")
        st.stop()

    # ===== 正文展示 =====
    for block in content:

        if isinstance(block, dict):

            if "table" in block:
                st.table(block["table"])

            elif "image" in block:
                st.image(block["image"])

        else:
            st.write(block)

    # ==================================================
    # 🤖 AI 分析
    # ==================================================
    st.markdown("---")
    st.subheader("🤖 AI 学术分析（基于当前主题）")

    question = st.text_input(
        "请输入你想让 AI 分析的问题"
    )

    if st.button("开始 AI 分析"):

        if not question.strip():
            st.warning("请输入问题")
            st.stop()

        text = "\n".join(t for t in content if isinstance(t, str))

        with st.spinner("🤖 AI 分析中..."):
            try:
                result = ai.ask_ai(question, text)
                st.markdown("### 🧠 AI 分析结果")
                st.write(result)
            except Exception as e:
                st.error(str(e))


# ==================================================
# 🔍 全文搜索
# ==================================================
if tab == "🔍 全文搜索":

    st.subheader("🔍 全文搜索")

    keyword = st.text_input("输入关键词")
    global_mode = st.checkbox("🌍 全局搜索（当前资料库）")

    if st.button("开始搜索"):

        if not keyword.strip():
            st.warning("请输入关键词")
            st.stop()

        if global_mode:

            root = os.path.join(
                "data",
                "电子书",
                collection
            )

            docs = glob.glob(
                os.path.join(root, "**", "*.docx"),
                recursive=True
            )

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

                idx += 1
