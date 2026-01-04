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
# Sidebar：文档选择（支持跳转）
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
# ✅ 可控 Tab（关键修复点）
# ==================================================
tab = st.radio(
    "功能区",
    ["📖 专栏 / 主题阅读", "🔍 全文搜索", "🤖 AI 分析"],
    horizontal=True,
    index=0 if st.session_state.force_read else 1
)


# ==================================================
# 📖 阅读区（跳转最终落点）
# ==================================================
if tab == "📖 专栏 / 主题阅读":
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
# 🔍 搜索区（高亮 + 跳转）
# ==================================================
if tab == "🔍 全文搜索":
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
# 🤖 AI 分析（改进版）
# ==================================================
if tab == "🤖 AI 分析":
    st.subheader("🤖 AI 学术辅助")



    # 第一步：选择分析对象
    source = st.radio(
        "分析对象",
        ["📖 当前主题", "📝 自定义文本"],
        horizontal=True
    )

    if source == "📖 当前主题":
        # 需要先在阅读区选择主题
        if "content" not in locals() or not content:
            st.warning("⚠️ 请先在「专栏 / 主题阅读」选择一个主题")
            st.stop()
        
        # 显示当前选中的主题信息
        st.info(f"📌 当前主题：**{st.session_state.jump_topic}**")
        
        # 提取内容
        text = "\n".join(
            t for t in content 
            if isinstance(t, str) and t.strip()
        )
        
        if not text:
            st.warning("该主题暂无文本内容")
            st.stop()
        
        st.text(f"内容长度：{len(text)} 字")

    else:  # 自定义文本
        text = st.text_area(
            "输入文本",
            height=200,
            placeholder="粘贴要分析的内容..."
        )
        if not text.strip():
            st.info("请输入分析内容")
            st.stop()

    st.divider()

    # 第二步：输入问题
    st.subheader("提问")
    user_question = st.text_input(
        "向 AI 提出你的问题",
        placeholder="例如：这个内容的核心观点是什么？",
        max_chars=500
    )

    # 第三步：分析按钮
    col1, col2 = st.columns([1, 4])
    with col1:
        analyze_btn = st.button("🚀 AI 分析", use_container_width=True)

    if analyze_btn:
        if not user_question.strip():
            st.warning("请输入问题")
            st.stop()

        # 调用 AI
        with st.spinner("🤔 AI 正在分析中..."):
            try:
                from logic import ai_engine as ai
                
                # 调用 ask_ai 函数
                response = ai.ask_ai(user_question, text)
                
                st.markdown("### 📋 分析结果")
                st.markdown(response)
                
                # 可选：添加下载按钮
                st.divider()
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        label="📥 下载结果",
                        data=response,
                        file_name="ai_analysis.txt",
                        mime="text/plain"
                    )
                
            except Exception as e:
                st.error(f"❌ 分析失败：{str(e)}")
