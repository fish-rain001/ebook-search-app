import streamlit as st
import threading

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
# 左侧：文档选择
# =========================
with st.sidebar:
    st.header("📂 文档选择")

    years = we.list_years()
    if not years:
        st.error("未检测到 data/电子书 目录")
        st.stop()

    year = st.selectbox("选择年份", years)

    issues = we.list_issues(year)
    if not issues:
        st.warning("该年份下未发现 Word 文件")
        st.stop()

    issue = st.selectbox("选择期刊", issues)

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
# 📖 Tab 1：专栏 → 主题 → 内容
# ==================================================
with tab_read:
    st.subheader("📖 按专栏 / 主题阅读")

    columns = we.list_columns(doc_path)
    if not columns:
        st.warning("文档中未识别到【标题1】专栏")
        st.stop()

    col1, col2 = st.columns([1, 2])

    with col1:
        column = st.selectbox("选择专栏", columns)

    topics = we.list_topics(doc_path, column)

    with col2:
        if topics:
            topic = st.selectbox("选择主题", topics)
        else:
            st.info("该专栏下未发现【标题2】主题")
            topic = None

    if topic:
        st.markdown("---")
        st.markdown(f"### {topic}")

        content = we.get_topic_content(doc_path, column, topic)

        if not content:
            st.info("该主题下无正文内容")
        else:
            for block in content:
                if isinstance(block, dict) and "table" in block:
                    st.table(block["table"])
                else:
                    st.write(block)

# ==================================================
# 🔍 Tab 2：全文搜索（完全复刻 Tkinter）
# ==================================================
with tab_search:
    st.subheader("🔍 全文搜索（标题 / 正文 / 表格）")

    keyword = st.text_input("输入关键词")

    if st.button("开始搜索"):
        if not keyword.strip():
            st.warning("请输入关键词")
        else:
            all_results = {
                "topics": [],
                "contents": [],
                "tables": []
            }
    
            # =========================
            # 情况 1：局部搜索（默认）
            # =========================
            if not global_mode:
                results = we.full_text_search(doc_path, keyword)
    
                all_results["topics"].extend(results["topics"])
                all_results["contents"].extend(results["contents"])
                all_results["tables"].extend(results["tables"])
    
            # =========================
            # 情况 2：全局搜索（所有 Word）
            # =========================
            else:
                book_root = os.path.join("data", "电子书")
                all_docs = glob.glob(
                    os.path.join(book_root, "**", "*.docx"),
                    recursive=True
                )
    
                with st.spinner(f"正在全局搜索 {len(all_docs)} 个 Word 文件..."):
                    for p in all_docs:
                        try:
                            results = we.full_text_search(p, keyword)
    
                            # 从路径中解析 年份 / 期刊
                            year = os.path.basename(os.path.dirname(p))
                            filename = os.path.basename(p)
    
                            for r in results["topics"]:
                                r["year"] = year
                                r["issue"] = filename
                                all_results["topics"].append(r)
    
                            for r in results["contents"]:
                                r["year"] = year
                                r["issue"] = filename
                                all_results["contents"].append(r)
    
                            for r in results["tables"]:
                                r["year"] = year
                                r["issue"] = filename
                                all_results["tables"].append(r)
    
                        except Exception as e:
                            # 单个文件出错不影响全局
                            continue
    
            # =========================
            # 结果展示
            # =========================
            total = (
                len(all_results["topics"])
                + len(all_results["contents"])
                + len(all_results["tables"])
            )
    
            if total == 0:
                st.info("未找到匹配内容")
            else:
                st.success(f"共找到 {total} 条结果")
    
                idx = 1
    
                for r in all_results["topics"]:
                    prefix = f"[{r.get('year','')}] {r.get('issue','')}"
                    with st.expander(
                        f"{idx}. 【标题】{prefix} ｜ {r['column']} → {r.get('topic','')}"
                    ):
                        st.write(r["hit"])
                    idx += 1
    
                for r in all_results["contents"]:
                    prefix = f"[{r.get('year','')}] {r.get('issue','')}"
                    with st.expander(
                        f"{idx}. 【正文】{prefix} ｜ {r['column']} → {r.get('topic','')}"
                    ):
                        st.write(r["content"])
                    idx += 1
    
                for r in all_results["tables"]:
                    prefix = f"[{r.get('year','')}] {r.get('issue','')}"
                    with st.expander(
                        f"{idx}. 【表格】{prefix} ｜ {r['column']} → {r.get('topic','')}（{r['location']}）"
                    ):
                        st.table(r["content"])
                    idx += 1


# ==================================================
# 🤖 Tab 3：AI 分析（非阻塞）
# ==================================================
with tab_ai:
    st.subheader("🤖 AI 学术辅助分析")

    source = st.radio(
        "分析对象",
        ["当前主题内容", "自定义文本"]
    )

    if source == "当前主题内容":
        if "topic" not in locals() or not topic:
            st.warning("请先在【专栏 / 主题阅读】中选择主题")
            st.stop()
        text = "\n".join(t for t in content if isinstance(t, str))
    else:
        text = st.text_area("输入分析文本", height=260)

    if st.button("开始 AI 分析"):
        if not text.strip():
            st.warning("内容不能为空")
        else:
            placeholder = st.empty()

            def run_ai():
                try:
                    summary = ai.summarize_text(text)
                    keywords = ai.extract_keywords(text)
                    analysis = ai.analyze_topic(text)

                    placeholder.markdown("### 📌 摘要")
                    placeholder.write(summary)

                    placeholder.markdown("### 🏷 关键词")
                    placeholder.write(keywords)

                    placeholder.markdown("### 🧠 学术分析")
                    placeholder.write(analysis)
                except Exception as e:
                    placeholder.error(str(e))

            threading.Thread(target=run_ai, daemon=True).start()



