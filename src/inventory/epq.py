"""经济生产批量 (EPQ) 模块"""
import streamlit as st
from src.utils.stats import fmt, parse_num
from src.utils.ui import result_value, result_grid, alert


def render_epq():
    st.markdown("## 🏭 经济生产批量 (EPQ)")
    st.caption("计算最优生产批量、生产周期、最大库存量及年总成本。适用于边生产边消耗的自制件场景。")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📋 输入参数")
        D = st.number_input("年需求率 D (件/年)", value=12000.0, step=100.0, key="epq_D")
        S = st.number_input("每次生产准备成本 S (元/次)", value=500.0, step=10.0, key="epq_S")
        H = st.number_input("单位年持有成本 H (元/件·年)", value=8.0, step=0.5, key="epq_H")
        p = st.number_input("日生产率 p (件/天)", value=100.0, step=1.0, key="epq_p")
        work_days = st.number_input("年工作天数", value=250.0, step=1.0, key="epq_days")
        C = st.number_input("单位生产成本 C (元/件，选填)", value=0.0, step=1.0, key="epq_C")

        if st.button("计算", key="epq_calc", use_container_width=True):
            if D <= 0 or S <= 0 or H <= 0 or p <= 0:
                alert("所有必填参数必须大于 0", "error")
            else:
                d = D / work_days
                if p <= d:
                    alert(f"生产率 p ({fmt(p)}) 必须大于日需求率 d ({fmt(d)} 件/天)，否则无法积累库存", "error")
                else:
                    _calc_epq(D, S, H, p, work_days, C)


def _calc_epq(D, S, H, p, work_days, C):
    """EPQ 计算"""
    d = D / work_days
    rho = d / p
    denom = H * (1 - rho)
    Q_star = (2 * D * S / denom) ** 0.5
    I_max = Q_star * (1 - rho)
    t_run = Q_star / p
    t_cycle = Q_star / d
    N = D / Q_star
    setup_cost = N * S
    hold_cost = (I_max / 2) * H
    product_cost = D * C if C > 0 else 0
    TC = setup_cost + hold_cost + product_cost

    # 对比 EOQ
    eoq = (2 * D * S / H) ** 0.5

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 📊 计算结果")
        st.metric("最优生产批量 Q*", f"{fmt(Q_star)} 件")
        result_grid([
            {"label": "最大库存量 I_max", "value": fmt(I_max), "unit": "件"},
            {"label": "年生产次数", "value": fmt(N), "unit": "次"},
            {"label": "生产运行时间", "value": fmt(t_run), "unit": "天"},
            {"label": "生产周期", "value": fmt(t_cycle), "unit": "天"},
            {"label": "年准备成本", "value": fmt(setup_cost), "unit": "元"},
            {"label": "年持有成本", "value": fmt(hold_cost), "unit": "元"},
        ])
        if C > 0:
            st.metric("年生产成本", f"{fmt(product_cost)} 元")
        st.metric("年总成本 TC", f"**{fmt(TC)}** 元")

    with col2:
        alert(
            f"与 EOQ 对比：若忽略边生产边消耗（按 EOQ），Q* = {fmt(eoq)} 件。"
            f"EPQ 批量更大，最大库存量 I_max = {fmt(I_max)} < EOQ 平均库存 {fmt(eoq/2)}。",
            "info"
        )

        # 库存积累图
        import plotly.graph_objects as go
        import numpy as np

        t = np.linspace(0, t_cycle * 2, 300)
        inv = []
        for ti in t:
            cycle_t = ti % t_cycle
            if cycle_t <= t_run:
                inv.append((p - d) * cycle_t)
            else:
                inv.append(I_max - d * (cycle_t - t_run))
        inv = np.maximum(np.array(inv), 0)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=t, y=inv, mode='lines', name='库存水平',
                                 fill='tozeroy', line=dict(color='#2563eb')))
        fig.add_hline(y=I_max, line_dash="dash", line_color="green",
                      annotation_text=f"I_max={fmt(I_max)}")
        fig.update_layout(title="库存积累-消耗周期", xaxis_title="时间 (天)",
                          yaxis_title="库存量 (件)", height=350)
        st.plotly_chart(fig, use_container_width=True)

    # 计算步骤
    with st.expander("📝 计算步骤", expanded=False):
        st.markdown(rf"""
        **1. 计算日需求率 d**
        $$d = \\frac{{D}}{{年工作天数}} = \\frac{{{fmt(D, 0)}}}{{{fmt(work_days, 0)}}} = \\textbf{{{fmt(d)} 件/天}}$$

        **2. 验证可行性**
        $$p = {fmt(p)} > d = {fmt(d)} \\quad ✅$$
        $$\\rho = d/p = {fmt(rho, 4)}$$（生产期间消耗比例）

        **3. 计算最优生产批量 Q\***
        $$Q^* = \\sqrt{{\\frac{{2DS}}{{H(1-d/p)}}}} = \\textbf{{{fmt(Q_star)} 件}}$$

        **4. 最大库存量**
        $$I_{{max}} = Q^* \\times (1 - d/p) = \\textbf{{{fmt(I_max)} 件}}$$

        **5. 年总成本**
        $$TC = 准备成本 + 持有成本 = {fmt(setup_cost)} + {fmt(hold_cost)} = \\textbf{{{fmt(TC)} 元}}$$
        """)
