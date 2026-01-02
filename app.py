import streamlit as st
from logic import word_engine as we
from logic import ai_engine as ai
import os

# =========================
# 页面配置
# =========================
st.set_page_config(
    page_title="电子书全文检索与分析系统",
    layout="wide"
)

st.title("📚 电子书全文检索与 AI 分析系统")

# =========================
# 左侧：文档选择
# =========================
with st.sidebar:
    st.header("📂 文档选择")

    years = we.list_years()
    if not years:
        st.error("未检测到电子书数据，请检查 data/电子书 目录")
        st.stop()

    year = st.selectbox("选择年份", years)

    issues = we.list_issues(year)
    if not issues:
        st.warning("该年份下未找到期刊文件")
        st.stop()

    issue = st.selectbox("选择期刊", issues)

    doc_path = we.find_doc_path(year, issue)
    if not doc_path or not os.path.exists(doc_path):
        st.error("未找到对应 Word 文件")
        st.stop()

    st.success(f"已加载：{os.path.basename(doc_path)}")

# =========================
# 页面 Tabs
# =========================
tab_search, tab_ai = st.tabs(
    ["🔍 全文搜索", "🤖 AI 分析"]
)

# ==================================================
# 🔍 Tab 1：全文搜索（完全复刻 Tkinter search_content）
# ==================================================
with tab_search:
    st.subheader("🔍 全文关键词搜索（标题 / 正文 / 表格）")

    keyword = st.text_input("请输入关键词")

    if st.button("开始搜索"):
        if not keyword.strip():
            st.warning("请输入关键词")
        else:
            with st.spinner("正在扫描文档，请稍候…"):
                result = we.full_text_search(doc_path, keyword)

            topic_hits = result.get("topics", [])
            content_hits = result.get("contents", [])
            table_hits = result.get("tables", [])

            total = len(topic_hits) + len(content_hits) + len(table_hits)

            if total == 0:
                st.info("未找到任何匹配内容")
            else:
                st.success(f"共找到 {total} 处匹配")

            # ========= 命中标题 =========
            if topic_hits:
                st.markdown("### 🏷️ 命中标题")
                for i, r in enumerate(topic_hits, start=1):
                    st.markdown(
                        f"**{i}. [{r['column']}]**"
                        + (f" → {r['topic']}" if r.get("topic") else "")
                    )
                    st.write(r["hit"])

            # ========= 命中正文 =========
            if content_hits:
                st.markdown("### 📄 命中正文")
                for i, r in enumerate(content_hits, start=1):
                    st.markdown(
                        f"**{i}. [{r['column']} → {r['topic']}]**"
                    )
                    st.write(r["content"])

            # ========= 命中表格 =========
            if table_hits:
                st.markdown("### 📊 命中表格")
                for i, r in enumerate(table_hits, start=1):
                    st.markdown(
                        f"**{i}. [{r['column']} → {r['topic']}] ({r['location']})**"
                    )
                    st.table(r["content"])

# ==================================================
# 🤖 Tab 2：AI 分析（不阻塞 UI）
# ==================================================
with tab_ai:
    st.subheader("🤖 AI 辅助分析（后台执行，不冻结界面）")

    st.info("AI 仅作为辅助工具，结果不替代人工判断")

    source = st.radio(
        "分析内容来源",
        ["从全文搜索结果复制", "自定义输入"]
    )

    if source == "从全文搜索结果复制":
        st.markdown(
            "请先在【全文搜索】中复制需要分析的内容，然后粘贴到下方。"
        )

    text = st.text_area(
        "分析文本",
        height=240
    )

    question = st.text_input(
        "你的分析问题（如：该专栏的主要观点是什么？）"
    )

    if st.button("🚀 开始 AI 分析"):
        if not text.strip():
            st.warning("分析文本不能为空")
        elif not question.strip():
            st.warning("问题不能为空")
        else:
            with st.spinner("AI 分析中，请稍候…"):
                try:
                    answer = ai.ask_ai(question, text)
                    st.markdown("### 💡 AI 分析结果")
                    st.write(answer)
                except Exception as e:
                    st.error(f"AI 调用失败：{e}")

