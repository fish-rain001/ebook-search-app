import os
import glob
import re
import threading
import html
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

st.title("📚 电子书专栏检索系统（Streamlit）")


# =========================
# 工具：高亮关键词
# =========================
def highlight_text(text, keyword):
    if not text or not keyword:
        return html.escape(text)

    escaped = html.escape(text)

    pattern = re.compile(re.escape(keyword), re.IGNORECASE)

    return pattern.sub(
        lambda m: f"<mark style='background-color:#ffe066'>{m.group(0)}</mark>",
        escaped
    )


# =========================
# 搜索缓存
# =========================
@st.cache_data(show_spinner=False)
def cached_full_text_search(doc_path, keyword):
    return we.full_text_search(doc_path, keyword)


@st.cache_data(show_spinner=False)
def cached_global_search(all_docs, keyword):
    results = {
        "topics": [],
        "contents": [],
        "tables": []
    }

    for p in all_docs:
        try:
            r = we.full_text_search(p, keyword)

            year = os.path.basename(os.path.dirname(p))
            issue = os.path.basename(p)

            for x in r["topics"]:
                x.update({"year": year, "issue": issue})
                results["topics"].append(x)

            for x in r["contents"]:
                x.update({"year": year, "issue": issue})
                results["contents"].append(x)

            for x in r["tables"]:
                x.update({"year": year, "issue": issue})
                results["tables"].append(x)

        except Exception:
            continue

    return results


# =========================
# 左侧：文档选择
# =========================
with st.sidebar:
    st.header("📂 文档选择")

    years = we.list_years()
    if not years:
        st.error("未检测到 data/电子书 目录")
        st.stop()

    year_index = (
        years.index(st.session_state["jump_year"])
        if "jump_year" in st.session_state and st.session_state["jump_year"] in years
        else 0
    )
    year = st.selectbox("选择年份", years, index=year_index)

    issues = we.list_issues(year)
    if not issues:
        st.warning("该年份下未发现 Word 文件")
        st.stop()

    issue_index = (
        issues.index(st.session_state["jump_issue"])
        if "jump_issue" in st.session_state and st.session_state["jump_issue"] in issues
        else 0
    )
    issue = st.selectbox("选择期刊", issues, index=issue_index)

    doc_path = we.find_doc_path(year, issue)
    if not doc_path:
        st.error("未找到对应 Word 文档")
        st.stop()


# =========================
# Tabs
# =========================
tab_read, tab_search, tab_ai = st.tabs(
    ["📖 专栏 / 主题阅读", "🔍 全文搜索", "🤖 AI 分析"]
)


# ==================================================
# 📖 Tab 1：阅读
# ==================================================
with tab_read:
    st.subheader("📖 按专栏 / 主题阅读")

    columns = we.list_columns(doc_path)
    if not columns:
        st.warning("文档中未识别到【标题1】专栏")
        st.stop()

    col1, col2 = st.columns([1, 2])

    column_index = (
        columns.index(st.session_state["jump_column"])
        if "jump_column" in st.session_state and st.session_state["jump_column"] in columns
        else 0
    )
    with col1:
        column = st.selectbox("选择专栏", columns, index=column_index)

    topics = we.list_topics(doc_path, column)

    topic_index = (
        topics.index(st.session_state["jump_topic"])
        if "jump_topic" in st.session_state and st.session_state["jump_topic"] in topics
        else 0
    )

    with col2:
        topic = st.selectbox("选择主题", topics, index=topic_index) if topics else None

    if topic:
        st.markdown("---")
        st.markdown(f"### {topic}")

        content = we.get_topic_content(doc_path, column, topic)

        for block in content:
            if isinstance(block, dict) and "table" in block:
                st.table(block["table"])
            else:
                st.write(block)


# ==================================================
# 🔍 Tab 2：全文搜索（含高亮）
# ==================================================
with tab_search:
    st.subheader("🔍 全文搜索（高亮命中词）")

    keyword = st.text_input("输入关键词")
    global_mode = st.checkbox("🌍 切换为全局搜索模式")

    if st.button("开始搜索"):
        if not keyword.strip():
            st.warning("请输入关键词")
            st.stop()

        if not global_mode:
            results = cached_full_text_search(doc_path, keyword)
        else:
            book_root = os.path.join("data", "电子书")
            all_docs = glob.glob(
                os.path.join(book_root, "**", "*.docx"),
                recursive=True
            )
            with st.spinner(f"正在全局搜索 {len(all_docs)} 个 Word 文件..."):
                results = cached_global_search(all_docs, keyword)

        total = len(results["topics"]) + len(results["contents"]) + len(results["tables"])

        if total == 0:
            st.info("未找到匹配内容")
            st.stop()

        st.success(f"共找到 {total} 条结果")
        idx = 1

        for r in results["topics"]:
            title = f"[{r.get('year','')}] {r.get('issue','')} ｜ {r['column']} → {r.get('topic','')}"
            with st.expander(f"{idx}. 【标题】{title}"):
                st.markdown(
                    highlight_text(r["hit"], keyword),
                    unsafe_allow_html=True
                )

                if st.button("📖 跳转阅读", key=f"jump_t_{idx}"):
                    st.session_state.update({
                        "jump_year": r.get("year"),
                        "jump_issue": r.get("issue"),
                        "jump_column": r.get("column"),
                        "jump_topic": r.get("topic")
                    })
                    st.experimental_rerun()
            idx += 1

        for r in results["contents"]:
            title = f"[{r.get('year','')}] {r.get('issue','')} ｜ {r['column']} → {r.get('topic','')}"
            with st.expander(f"{idx}. 【正文】{title}"):
                st.markdown(
                    highlight_text(r["content"], keyword),
                    unsafe_allow_html=True
                )

                if st.button("📖 跳转阅读", key=f"jump_c_{idx}"):
                    st.session_state.update({
                        "jump_year": r.get("year"),
                        "jump_issue": r.get("issue"),
                        "jump_column": r.get("column"),
                        "jump_topic": r.get("topic")
                    })
                    st.experimental_rerun()
            idx += 1

        for r in results["tables"]:
            title = f"[{r.get('year','')}] {r.get('issue','')} ｜ {r['column']} → {r.get('topic','')}"
            with st.expander(f"{idx}. 【表格】{title}"):
                highlighted_rows = [
                    [highlight_text(c, keyword) for c in row]
                    for row in r["content"]
                ]
                st.markdown(
                    "<br>".join([" | ".join(row) for row in highlighted_rows]),
                    unsafe_allow_html=True
                )
            idx += 1


# ==================================================
# 🤖 Tab 3：AI 分析
# ==================================================
with tab_ai:
    st.subheader("🤖 AI 学术辅助分析")

    source = st.radio("分析对象", ["当前主题内容", "自定义文本"])

    if source == "当前主题内容":
        if not topic:
            st.warning("请先选择主题")
            st.stop()
        text = "\n".join(t for t in content if isinstance(t, str))
    else:
        text = st.text_area("输入分析文本", height=260)

    if st.button("开始 AI 分析"):
        placeholder = st.empty()

        def run_ai():
            try:
                placeholder.markdown("### 📌 摘要")
                placeholder.write(ai.summarize_text(text))
                placeholder.markdown("### 🏷 关键词")
                placeholder.write(ai.extract_keywords(text))
                placeholder.markdown("### 🧠 学术分析")
                placeholder.write(ai.analyze_topic(text))
            except Exception as e:
                placeholder.error(str(e))

        threading.Thread(target=run_ai).start()




