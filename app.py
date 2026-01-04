# app.py
import streamlit as st
import os
import word_engine as we

# ======================
# 基本配置
# ======================
st.set_page_config(
    page_title="电子书专栏检索系统",
    layout="wide"
)

BASE_DIR = "电子书"   # ⚠️ 云端可改成 "./data" 或挂载目录

st.title("📚 电子书专栏检索系统（Streamlit 版）")

# ======================
# Session State
# ======================
if "search_result" not in st.session_state:
    st.session_state.search_result = None

# ======================
# 左侧：检索条件
# ======================
with st.sidebar:
    st.header("🔎 检索条件")

    years = we.list_years(BASE_DIR)
    year = st.selectbox("年份", ["所有"] + years)

    issues = we.list_issues(BASE_DIR, year)
    issue = st.selectbox("期刊号", ["所有"] + issues)

    columns = we.list_columns(BASE_DIR, year, issue)
    column = st.selectbox("专栏", ["所有"] + columns)

    keyword = st.text_input("全文搜索关键词")

    do_search = st.button("🔍 执行全文搜索")

# ======================
# 执行全文搜索
# ======================
if do_search:
    if not keyword.strip():
        st.warning("请输入搜索关键词")
    else:
        with st.spinner("正在全文检索，请稍候..."):
            st.session_state.search_result = we.full_text_search(
                base_dir=BASE_DIR,
                keyword=keyword.strip(),
                year=year,
                issue=issue,
                column=column
            )

# ======================
# 结果展示
# ======================
result = st.session_state.search_result

if result:
    topics   = result.get("topics", [])
    contents = result.get("contents", [])
    tables   = result.get("tables", [])

    all_results = []
    all_results.extend(topics)
    all_results.extend(contents)
    all_results.extend(tables)

    st.subheader(f"✅ 共找到 {len(all_results)} 条结果")

    if not all_results:
        st.info("没有找到匹配内容")
    else:
        for i, r in enumerate(all_results, 1):

            # ========= 标题 =========
            title_parts = []
            if r.get("section"):
                title_parts.append(r["section"])
            if r.get("topic"):
                title_parts.append(r["topic"])

            title = " → ".join(title_parts) if title_parts else "搜索结果"

            with st.expander(f"{i}. {title}", expanded=False):

                # ========= 元信息 =========
                meta = []
                if r.get("year"):
                    meta.append(f"📅 {r['year']}年")
                if r.get("issue"):
                    meta.append(f"📖 {r['issue']}")
                if meta:
                    st.caption(" | ".join(meta))

                # ========= 正文 =========
                if r.get("content"):
                    st.markdown(r["content"])

                # ========= 表格 =========
                if r.get("table"):
                    st.text(r["table"])

                # ========= 兜底 =========
                if not r.get("content") and not r.get("table"):
                    st.warning("该结果没有正文内容")

# ======================
# 说明
# ======================
st.markdown("---")
st.caption(
    "✔ 专栏 = Word 中「标题1」\n"
    "✔ 主题 = Word 中「标题2」\n"
    "✔ 正文 / 表格 = 标题2 下内容\n"
    "✔ 已完整复刻 Tkinter 搜索语义"
)


