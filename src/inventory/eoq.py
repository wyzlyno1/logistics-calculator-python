"""经济订货批量 (EOQ) 模块"""
import streamlit as st
from src.utils.stats import fmt, parse_num
from src.utils.ui import result_value, result_grid, steps_card, alert


def render_eoq():
    st.markdown("## 📦 经济订货批量 (EOQ)")
    st.caption("基于经典 EOQ 模型，计算使年库存总成本最小的订货批量。支持基本 EOQ、数量折扣分析和允许缺货模型。")

    tab1, tab2, tab3 = st.tabs(["基本 EOQ", "数量折扣", "允许缺货"])

    with tab1:
        _render_basic_eoq()
    with tab2:
        _render_discount_eoq()
    with tab3:
        _render_shortage_eoq()


def _render_basic_eoq():
    """基本 EOQ"""
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 📋 输入参数")
        D = st.number_input("年需求量 D (件/年)", value=12000.0, step=100.0, key="eoq_basic_D")
        S = st.number_input("每次订货成本 S (元/次)", value=200.0, step=10.0, key="eoq_basic_S")
        H = st.number_input("单位年持有成本 H (元/件·年)", value=5.0, step=0.5, key="eoq_basic_H")
        C = st.number_input("单位采购成本 C (元/件，选填)", value=0.0, step=1.0, key="eoq_basic_C")
        L = st.number_input("提前期 L (天，选填)", value=0.0, step=1.0, key="eoq_basic_L")
        work_days = st.number_input("年工作天数", value=365.0, step=1.0, key="eoq_basic_days")

        if st.button("计算", key="eoq_basic_calc", use_container_width=True):
            if D <= 0 or S <= 0 or H <= 0:
                alert("所有参数必须大于 0", "error")
            else:
                _calc_basic(D, S, H, C, L, work_days)


def _calc_basic(D, S, H, C, L, work_days):
    """基本 EOQ 计算"""
    Q_star = (2 * D * S / H) ** 0.5
    N = D / Q_star
    order_cost = N * S
    hold_cost = (Q_star / 2) * H
    purchase_cost = D * C if C > 0 else 0
    TC = order_cost + hold_cost + purchase_cost
    T_cycle = work_days / N
    d = D / work_days
    ROP = d * L if L > 0 else 0

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 📊 计算结果")
        st.metric("最优订货量 Q*", f"{fmt(Q_star)} 件")
        result_grid([
            {"label": "年订货次数 N", "value": fmt(N), "unit": "次"},
            {"label": "订货周期 T", "value": fmt(T_cycle), "unit": "天"},
            {"label": "年订货成本", "value": fmt(order_cost), "unit": "元"},
            {"label": "年持有成本", "value": fmt(hold_cost), "unit": "元"},
        ])
        if C > 0:
            st.metric("年采购成本", f"{fmt(purchase_cost)} 元")
        st.metric("年总成本 TC", f"**{fmt(TC)}** 元")
        if L > 0:
            st.metric("再订货点 ROP", f"{fmt(ROP)} 件")
            st.caption(f"当库存降至 {fmt(ROP)} 件时，发出订货请求")

    with col2:
        # 成本曲线图
        import plotly.graph_objects as go
        import numpy as np

        Q_range = np.linspace(Q_star * 0.2, Q_star * 2.5, 200)
        oc = (D / Q_range) * S
        hc = (Q_range / 2) * H
        tc = oc + hc

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=Q_range, y=oc, mode='lines', name='年订货成本', line=dict(color='#ef4444')))
        fig.add_trace(go.Scatter(x=Q_range, y=hc, mode='lines', name='年持有成本', line=dict(color='#2563eb')))
        fig.add_trace(go.Scatter(x=Q_range, y=tc, mode='lines', name='年总成本', line=dict(color='#10b981', width=2.5)))
        fig.add_vline(x=Q_star, line_dash="dash", line_color="gray", annotation_text=f"Q*={fmt(Q_star)}")
        fig.update_layout(
            title="成本曲线",
            xaxis_title="订货量 Q (件)",
            yaxis_title="年成本 (元)",
            hovermode="x unified",
            height=350,
        )
        st.plotly_chart(fig, use_container_width=True)

    # 计算步骤
    with st.expander("📝 计算步骤", expanded=False):
        st.markdown(rf"""
        **1. 计算最优订货量 Q\***
        $$Q^* = \\sqrt{{\\frac{{2DS}}{{H}}}} = \\sqrt{{\\frac{{2 \\times {fmt(D, 0)} \\times {fmt(S)}}}{{{fmt(H)}}}}} = \\sqrt{{{fmt(2*D*S, 0)}}} = \\textbf{{{fmt(Q_star)} 件}}$$

        **2. 计算年订货次数 N**
        $$N = \\frac{{D}}{{Q^*}} = \\frac{{{fmt(D, 0)}}}{{{fmt(Q_star)}}} = \\textbf{{{fmt(N)} 次/年}}$$

        **3. 计算年订货成本**
        $$年订货成本 = N \\times S = {fmt(N)} \\times {fmt(S)} = \\textbf{{{fmt(order_cost)} 元}}$$

        **4. 计算年持有成本**
        $$年持有成本 = \\frac{{Q^*}}{{2}} \\times H = \\frac{{{fmt(Q_star)}}}{{2}} \\times {fmt(H)} = \\textbf{{{fmt(hold_cost)} 元}}$$

        **5. 计算年总成本**
        $$TC = \\textbf{{{fmt(TC)} 元}}$$
        """)
        if L > 0:
            st.latex(f"ROP = d \\times L = {fmt(d)} \\times {fmt(L)} = \\textbf{{{fmt(ROP)} 件}}")


def _render_discount_eoq():
    """数量折扣 EOQ"""
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 📋 输入参数")
        D = st.number_input("年需求量 D (件/年)", value=12000.0, step=100.0, key="eod_D")
        S = st.number_input("每次订货成本 S (元/次)", value=200.0, step=10.0, key="eod_S")
        I = st.number_input("年持有成本比例 I (小数)", value=0.2, step=0.01, key="eod_I")
        st.caption("折扣方案（每行：最低订货量, 单价）")
        tiers_text = st.text_area(
            "折扣方案",
            value="0, 10.00\n1000, 9.50\n2000, 9.00",
            height=120,
            key="eod_tiers",
        )

        if st.button("计算", key="eod_calc", use_container_width=True):
            _calc_discount(D, S, I, tiers_text)


def _calc_discount(D, S, I, tiers_text):
    """数量折扣 EOQ 计算"""
    import pandas as pd

    # 解析折扣层级
    tiers = []
    for line in tiers_text.strip().split('\n'):
        parts = line.replace(',', ' ').replace('，', ' ').split()
        if len(parts) >= 2:
            qty = parse_num(parts[0])
            price = parse_num(parts[1])
            if not (qty != qty or price != price):
                tiers.append({"qty_min": qty, "price": price})

    if len(tiers) < 2:
        alert("请至少输入两个折扣层级", "error")
        return

    tiers.sort(key=lambda t: t["qty_min"])

    # 对每个层级计算
    results = []
    for i, tier in enumerate(tiers):
        H = tier["price"] * I
        Q = (2 * D * S / H) ** 0.5
        lower = tier["qty_min"]
        upper = tiers[i + 1]["qty_min"] - 1 if i < len(tiers) - 1 else float('inf')

        feasible_Q = Q
        note = ""
        if Q < lower:
            feasible_Q = lower
            note = f"Q*({fmt(Q)}) 低于区间下限，调整为 {fmt(lower)}"
        elif Q > upper:
            feasible_Q = None
            note = f"Q*({fmt(Q)}) 高于区间上限，不可行"
        else:
            note = f"可行区间 [{fmt(lower)}, {'∞' if upper == float('inf') else fmt(upper)}]"

        TC = float('inf')
        if feasible_Q is not None:
            TC = (D / feasible_Q) * S + (feasible_Q / 2) * H + D * tier["price"]

        results.append({
            "层级": i + 1,
            "最低订货量": tier["qty_min"],
            "单价": tier["price"],
            "H=I×C": H,
            "Q*理论值": Q,
            "可行订货量": feasible_Q,
            "年总成本": TC,
            "备注": note,
        })

    # 找最优
    best = min([r for r in results if r["可行订货量"] is not None], key=lambda r: r["年总成本"])

    # 结果展示
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 📊 计算结果")
        st.metric("最优订货量 Q*", f"{fmt(best['可行订货量'])} 件")
        st.metric("对应单价", f"{fmt(best['单价'])} 元/件")
        st.metric("年总成本", f"{fmt(best['年总成本'])} 元")

    with col2:
        st.markdown("#### 📋 各层级对比")
        df = pd.DataFrame(results)
        df_display = df.copy()
        for col_name in ["单价", "H=I×C", "Q*理论值", "年总成本"]:
            if col_name in df_display.columns:
                df_display[col_name] = df_display[col_name].apply(
                    lambda x: fmt(x) if x != float('inf') else '—'
                )
        df_display["可行订货量"] = df_display["可行订货量"].apply(
            lambda x: fmt(x) if x is not None else '—'
        )
        st.dataframe(df_display, use_container_width=True, hide_index=True)

    # 成本柱状图
    import plotly.graph_objects as go
    valid = [r for r in results if r["可行订货量"] is not None]
    fig = go.Figure(data=[
        go.Bar(
            x=[f"层级{r['层级']}" for r in valid],
            y=[r["年总成本"] for r in valid],
            text=[fmt(r["年总成本"]) for r in valid],
            textposition='outside',
            marker_color=['#ef4444' if r == best else '#94a3b8' for r in valid],
        )
    ])
    fig.update_layout(title="各层级年总成本对比", yaxis_title="年总成本 (元)", height=350)
    st.plotly_chart(fig, use_container_width=True)


def _render_shortage_eoq():
    """允许缺货 EOQ"""
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 📋 输入参数")
        D = st.number_input("年需求量 D (件/年)", value=12000.0, step=100.0, key="eos_D")
        S = st.number_input("每次订货成本 S (元/次)", value=200.0, step=10.0, key="eos_S")
        H = st.number_input("单位年持有成本 H (元/件·年)", value=5.0, step=0.5, key="eos_H")
        B = st.number_input("单位年缺货成本 B (元/件·年)", value=10.0, step=1.0, key="eos_B")
        C = st.number_input("单位采购成本 C (元/件，选填)", value=0.0, step=1.0, key="eos_C")

        if st.button("计算", key="eos_calc", use_container_width=True):
            if D <= 0 or S <= 0 or H <= 0 or B <= 0:
                alert("所有参数必须大于 0", "error")
            else:
                _calc_shortage(D, S, H, B, C)


def _calc_shortage(D, S, H, B, C):
    """允许缺货 EOQ 计算"""
    fac = (H + B) / B
    Q_star = (2 * D * S / H) ** 0.5 * (fac ** 0.5)
    S_max = Q_star * (B / (H + B))
    shortage = Q_star - S_max
    hold_cost = (S_max ** 2) / (2 * Q_star) * H
    order_cost = (D / Q_star) * S
    shortage_cost = ((Q_star - S_max) ** 2) / (2 * Q_star) * B
    purchase_cost = D * C if C > 0 else 0
    TC = order_cost + hold_cost + shortage_cost + purchase_cost
    N = D / Q_star

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 📊 计算结果")
        st.metric("最优订货量 Q*", f"{fmt(Q_star)} 件")
        result_grid([
            {"label": "最大库存量 S_max", "value": fmt(S_max), "unit": "件"},
            {"label": "最大缺货量", "value": fmt(shortage), "unit": "件"},
            {"label": "年订货次数", "value": fmt(N), "unit": "次"},
            {"label": "年订货成本", "value": fmt(order_cost), "unit": "元"},
            {"label": "年持有成本", "value": fmt(hold_cost), "unit": "元"},
            {"label": "年缺货成本", "value": fmt(shortage_cost), "unit": "元"},
        ])
        if C > 0:
            st.metric("年采购成本", f"{fmt(purchase_cost)} 元")
        st.metric("年总成本 TC", f"**{fmt(TC)}** 元")

    # 库存周期图
    import plotly.graph_objects as go
    import numpy as np
    T_cycle = Q_star / (D / 365)
    t = np.linspace(0, T_cycle * 1.5, 300)
    inv = []
    for ti in t:
        cycle_t = ti % T_cycle
        if cycle_t <= T_cycle * (S_max / Q_star):
            inv.append(S_max - (D / 365) * cycle_t)
        else:
            inv.append(0)
    inv = np.array(inv)
    inv = np.maximum(inv, -(Q_star - S_max))

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=t, y=inv, mode='lines', name='库存水平',
                             fill='tozeroy', line=dict(color='#2563eb')))
    fig.add_hline(y=0, line_dash="solid", line_color="gray")
    fig.add_hline(y=S_max, line_dash="dash", line_color="green", annotation_text="S_max")
    fig.update_layout(title="库存水平变化", xaxis_title="时间 (天)", yaxis_title="库存量 (件)", height=350)
    st.plotly_chart(fig, use_container_width=True)
