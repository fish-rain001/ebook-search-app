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
    "force_read", "current_tab"
]:
    if k not in st.session_state:
        st.session_state[k] = None

if st.session_state.current_tab is None:
    st.session_state.current_tab = 0


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
# Sidebar：文档选择（支持跳转）
# ==================================================
with st.sidebar:
    st.header("📂 文档选择")

    years = we.list_years()
    if not years:
        st.error("未检测到 data/电子书")
        st.stop()

    # 🔑 优先使用 jump_year，否则用第一个
    if st.session_state.jump_year and st.session_state.jump_year in years:
        year = st.session_state.jump_year
        year_idx = years.index(year)
        st.session_state.jump_year = None  # 立即清空，防止重复
    else:
        year = years[0]
        year_idx = 0

    year = st.selectbox("选择年份", years, index=year_idx)

    issues = we.list_issues(year)
    if not issues:
        st.warning("该年份无期刊")
        st.stop()

    if st.session_state.jump_issue and st.session_state.jump_issue in issues:
        issue = st.session_state.jump_issue
        issue_idx = issues.index(issue)
        st.session_state.jump_issue = None  # 立即清空
    else:
        issue = issues[0]
        issue_idx = 0

    issue = st.selectbox("选择期刊", issues, index=issue_idx)

    doc_path = we.find_doc_path(year, issue)
    if not doc_path:
        st.error("未找到 Word")
        st.stop()


# ==================================================
# Tab 选择
# ==================================================
tab_options = ["📖 专栏 / 主题阅读", "🔍 全文搜索", "🤖 AI 分析"]

# 如果强制读取，必须切到第一个 tab
if st.session_state.force_read:
    st.session_state.current_tab = 0
    st.session_state.force_read = False

tab_index = st.session_state.current_tab if st.session_state.current_tab is not None else 0
tab = st.radio(
    "功能区",
    tab_options,
    horizontal=True,
    index=tab_index
)

st.session_state.current_tab = tab_options.index(tab)


# ==================================================
# 📖 阅读区（跳转最终落点）
# ==================================================
if tab == "📖 专栏 / 主题阅读":
    st.subheader("📖 按专栏 / 主题阅读")

    columns = we.list_columns(doc_path)
    if not columns:
        st.warning("未识别到专栏")
        st.stop()

    # 🔑 直接使用 jump_column，避免 selectbox 的复杂逻辑
    if st.session_state.jump_column and st.session_state.jump_column in columns:
        column = st.session_state.jump_column
        column_idx = columns.index(column)
        st.session_state.jump_column = None
    else:
        column = columns[0]
        column_idx = 0

    c1, c2 = st.columns([1, 2])
    with c1:
        column = st.selectbox("选择专栏", columns, index=column_idx)

    topics = we.list_topics(doc_path, column)
    if not topics:
        st.info("该专栏无主题")
        st.stop()

    if st.session_state.jump_topic and st.session_state.jump_topic in topics:
        topic = st.session_state.jump_topic
        topic_idx = topics.index(topic)
        st.session_state.jump_topic = None
    else:
        topic = topics[0]
        topic_idx = 0

    with c2:
        topic = st.selectbox("选择主题", topics, index=topic_idx)

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
# 🔍 搜索区（高亮 + 跳转）
# ==================================================
elif tab == "🔍 全文搜索":
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
        
        # 🔑 先收集所有结果到列表
        all_results = []
        for group in ["topics", "contents", "tables"]:
            for r in results[group]:
                all_results.append((group, r))
        
        # 显示结果
        for idx, (group, r) in enumerate(all_results, 1):
            title = f"[{r.get('year','')}] {r.get('issue','')} ｜ {r.get('column','')} → {r.get('topic','')}"
            
            with st.expander(f"{idx}. {title}"):
                # 显示内容
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
                
                # 分开一行放按钮和调试
                col1, col2 = st.columns([1, 4])
                
                with col1:
                    if st.button("📖 跳转", key=f"jump_btn_{idx}"):
                        st.write("✅ 按钮被点击了")
                        st.write(f"Year: {r.get('year')}")
                        st.write(f"Issue: {r.get('issue')}")
                
                with col2:
                    st.caption(f"原始数据: year={r.get('year')}, issue={r.get('issue')}, column={r.get('column')}, topic={r.get('topic')}")


# ==================================================
# 🤖 AI 分析
# ==================================================
elif tab == "🤖 AI 分析":
    st.subheader("🤖 AI 学术辅助")

    source = st.radio("分析对象", ["当前主题", "自定义文本"])

    if source == "当前主题":
        if "content" not in locals():
            st.warning("请先选择主题")
            st.stop()
        text = "\n".join(t for t in content if isinstance(t, str))
    else:
        text = st.text_area("输入文本", height=260)

    if st.button("开始分析"):
        placeholder = st.empty()

        def run_ai():
            try:
                with placeholder.container():
                    st.markdown("### 📌 摘要")
                    st.write(ai.summarize_text(text))
                    st.markdown("### 🏷 关键词")
                    st.write(ai.extract_keywords(text))
                    st.markdown("### 🧠 分析")
                    st.write(ai.analyze_topic(text))
            except Exception as e:
                placeholder.error(str(e))

        threading.Thread(target=run_ai).start()
