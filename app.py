"""
物流计算工具箱 — Streamlit 版
==============================

面向物流工程专业的综合性计算平台，覆盖库存管理、物流规划、需求预测三大领域共10个核心算法模块。

架构说明：
- app.py 只负责侧边栏导航和模块路由，不包含任何计算逻辑
- 每个模块的 render_xxx() 函数在 src/ 对应目录下
- 计算逻辑与 UI 分离：src/*/xxx.py 可独立导入使用，不依赖 Streamlit
- 算法公式完全照搬物流工程教材标准公式

运行方式：
    streamlit run app.py
"""
import streamlit as st

# 页面配置
st.set_page_config(
    page_title="物流计算工具箱",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 模块注册
MODULES = {
    "库存管理": [
        {"id": "eoq", "name": "经济订货批量 (EOQ)", "icon": "📦"},
        {"id": "epq", "name": "经济生产批量 (EPQ)", "icon": "🏭"},
        {"id": "safety_stock", "name": "安全库存计算", "icon": "🛡️"},
        {"id": "abc", "name": "ABC 分类分析", "icon": "📊"},
    ],
    "物流规划": [
        {"id": "gravity", "name": "重心法选址", "icon": "📍"},
        {"id": "location", "name": "选址案例分析", "icon": "🏢"},
        {"id": "transportation", "name": "运输问题求解", "icon": "🚚"},
        {"id": "network", "name": "物流网络优化", "icon": "🕸️"},
    ],
    "需求管理": [
        {"id": "forecasting", "name": "需求预测方法", "icon": "📈"},
        {"id": "bullwhip", "name": "牛鞭效应演示", "icon": "🐂"},
    ],
}


def main():
    # 侧边栏
    with st.sidebar:
        # 侧边栏头像（可以放自己的 GitHub 头像或其他图片链接）
        # st.image("https://avatars.githubusercontent.com/your-username", width=64)
        st.title("物流计算工具箱")
        st.caption("by 湫 · 物流工程")

        st.divider()

        # 导航
        if "current_module" not in st.session_state:
            st.session_state.current_module = None

        # 首页按钮
        if st.button("🏠 首页", use_container_width=True):
            st.session_state.current_module = None

        st.divider()

        # 分类导航
        for category, modules in MODULES.items():
            st.markdown(f"**{category}**")
            for mod in modules:
                label = f"{mod['icon']} {mod['name']}"
                if st.button(label, key=mod["id"], use_container_width=True):
                    st.session_state.current_module = mod["id"]
            st.markdown("")

        st.divider()
        st.caption("© 2026 湫 · 营口理工学院")

    # 主内容区
    current = st.session_state.current_module

    if current is None:
        render_home()
    elif current == "eoq":
        from src.inventory.eoq import render_eoq
        render_eoq()
    elif current == "epq":
        from src.inventory.epq import render_epq
        render_epq()
    elif current == "safety_stock":
        from src.inventory.safety_stock import render_safety_stock
        render_safety_stock()
    elif current == "abc":
        from src.inventory.abc import render_abc
        render_abc()
    elif current == "gravity":
        from src.planning.gravity import render_gravity
        render_gravity()
    elif current == "location":
        from src.planning.location import render_location
        render_location()
    elif current == "transportation":
        from src.planning.transportation import render_transportation
        render_transportation()
    elif current == "network":
        from src.planning.network import render_network
        render_network()
    elif current == "forecasting":
        from src.demand.forecasting import render_forecasting
        render_forecasting()
    elif current == "bullwhip":
        from src.demand.bullwhip import render_bullwhip
        render_bullwhip()


def render_home():
    """首页欢迎页"""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 40px 0;">
            <h1>📦 物流计算工具箱</h1>
            <p style="font-size: 1.1rem; color: #64748b;">
                物流工程课程辅助工具 · 覆盖库存管理、物流规划、需求预测等核心计算
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    for category, modules in MODULES.items():
        st.markdown(f"### {category}")
        cols = st.columns(len(modules))
        for col, mod in zip(cols, modules):
            with col:
                with st.container(border=True):
                    st.markdown(f"#### {mod['icon']} {mod['name']}")
                    if st.button("进入", key=f"home_{mod['id']}", use_container_width=True):
                        st.session_state.current_module = mod["id"]
                        st.rerun()

    st.divider()
    st.markdown("""
    <div style="text-align: center; color: #94a3b8; font-size: 0.85rem; padding: 20px 0;">
        纯 Python 实现 · Streamlit + Plotly · 所有计算基于物流工程教材标准公式<br>
        © 2026 湫 · 营口理工学院 · 物流工程专业
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
