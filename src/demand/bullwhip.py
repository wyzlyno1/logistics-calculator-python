"""牛鞭效应演示器 — 四级供应链需求放大模拟"""
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from src.utils.stats import fmt, parse_num


def render_bullwhip():
    st.markdown("## 🐂 牛鞭效应演示")
    st.caption("模拟四级供应链（零售商→批发商→分销商→制造商），直观展示需求信息逐级放大的牛鞭效应。")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("#### ⚙️ 模拟参数")
        T = st.number_input("模拟周期数", value=30, min_value=10, max_value=200, step=10, key="bw_periods")
        mean = st.number_input("客户需求均值 d̄ (件/周期)", value=100.0, step=10.0, key="bw_mean")
        sigma = st.number_input("需求标准差 σ", value=20.0, min_value=0.0, step=5.0, key="bw_sigma")
        L = st.number_input("各级提前期 L (周期)", value=2, min_value=1, max_value=10, step=1, key="bw_leadtime")
        Z = st.number_input("安全系数 Z", value=1.645, min_value=0.0, max_value=4.0, step=0.01, key="bw_z")
        n_MA = st.number_input("移动平均期数 (预测用)", value=5, min_value=2, max_value=20, step=1, key="bw_ma")
        init_stock = st.number_input("初始库存 (件)", value=500.0, min_value=0.0, step=50.0, key="bw_init")

        st.caption("""
        模拟逻辑：
        - 每级用移动平均法预测下游需求
        - 按 order-up-to 策略订货
        - 牛鞭比 = Var(本级订单) / Var(客户需求)
        """)

        if st.button("▶ 运行模拟", key="bw_run", use_container_width=True):
            _run_bullwhip(int(T), mean, sigma, L, Z, n_MA, init_stock)


def _run_bullwhip(T, mean, sigma, L, Z, n_MA, init_stock):
    """运行牛鞭效应模拟"""
    np.random.seed(42)

    # 生成客户需求（正态分布，非负）
    demand = np.random.normal(mean, sigma, T)
    demand = np.maximum(10, np.round(demand))

    names = ['零售商 Retailer', '批发商 Wholesaler', '分销商 Distributor', '制造商 Manufacturer']
    echelons = 4

    # 状态数组
    orders = [[] for _ in range(echelons)]
    inventory = [[] for _ in range(echelons)]
    backorder = [[] for _ in range(echelons)]
    stock = [init_stock] * echelons
    bo = [0.0] * echelons

    for t in range(T):
        for e in range(echelons):
            # 1. 到货
            if t >= L and len(orders[e]) > t - L:
                stock[e] += orders[e][t - L]

            # 2. 满足下游需求
            if e == 0:
                downstream = demand[t]
            else:
                downstream = orders[e - 1][t] if t < len(orders[e - 1]) else mean

            fulfilled = min(stock[e], downstream + bo[e])
            stock[e] -= fulfilled
            new_bo = downstream + bo[e] - fulfilled
            bo[e] = new_bo
            backorder[e].append(new_bo)
            inventory[e].append(stock[e])

            # 3. 预测下游需求（移动平均）
            if e == 0:
                hist = demand[max(0, t - n_MA + 1):t + 1]
            else:
                hist = np.array(orders[e - 1][max(0, t - n_MA + 1):t + 1])
            forecast = np.mean(hist) if len(hist) > 0 else mean

            # 4. Order-up-to 策略
            order_up_to = forecast * (L + 1) + Z * sigma * np.sqrt(L + 1)
            prev_order = orders[e][t - 1] if t > 0 and len(orders[e]) > t - 1 else 0
            order_qty = max(0.0, np.round(order_up_to - stock[e] - prev_order + bo[e]))
            orders[e].append(order_qty)

    # 计算牛鞭比
    demand_var = np.var(demand, ddof=0)
    bullwhip_ratios = []
    for e in range(echelons):
        order_var = np.var(orders[e], ddof=0) if len(orders[e]) > 0 else 0
        bullwhip_ratios.append(order_var / demand_var if demand_var > 0 else 0)

    # ==== 结果展示 ====
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("#### 📊 牛鞭比")
        ratio_cols = st.columns(4)
        colors = ['#2563eb', '#ef4444', '#f59e0b', '#10b981']
        for i, (col, ratio) in enumerate(zip(ratio_cols, bullwhip_ratios)):
            with col:
                st.metric(names[i].split()[0], f"{fmt(ratio, 2)}×")

        st.markdown("#### 📈 统计汇总")
        st.metric("客户需求方差", fmt(demand_var, 0))
        st.metric("零售商订单方差", fmt(np.var(orders[0], ddof=0), 0))
        st.metric("制造商订单方差", fmt(np.var(orders[3], ddof=0), 0))

        avg_ratio = np.mean(bullwhip_ratios)
        if avg_ratio < 1.3:
            alert("牛鞭效应轻微——供应链协调良好", "success")
        elif avg_ratio < 2.5:
            alert("牛鞭效应明显——建议信息共享或缩短提前期", "warning")
        else:
            alert("牛鞭效应严重——需求被显著放大，上游面临巨大库存压力", "error")

    with col_b:
        # 需求波动对比图
        fig = go.Figure()
        datasets = [
            (demand, '#94a3b8', '客户需求', 3),
            (np.array(orders[0]), '#2563eb', names[0], 2),
            (np.array(orders[1]), '#ef4444', names[1], 2),
            (np.array(orders[2]), '#f59e0b', names[2], 2),
            (np.array(orders[3]), '#10b981', names[3], 2),
        ]
        for data_arr, color, label, width in datasets:
            var_ratio = fmt(np.var(data_arr, ddof=0) / demand_var, 2) if demand_var > 0 else '0'
            fig.add_trace(go.Scatter(
                x=list(range(1, T + 1)), y=data_arr,
                mode='lines', name=f'{label} ({var_ratio}×)',
                line=dict(color=color, width=width),
            ))

        fig.update_layout(
            title="需求波动对比（客户需求 vs 各级订单量）",
            xaxis_title="周期", yaxis_title="数量 (件)",
            height=400, hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True)

    # 详细数据表
    with st.expander("📋 模拟数据明细", expanded=False):
        df_data = {"周期": list(range(1, T + 1)), "客户需求": demand}
        for e in range(echelons):
            df_data[f"{names[e]}订单"] = orders[e]
            df_data[f"{names[e]}库存"] = inventory[e]
        st.dataframe(pd.DataFrame(df_data), use_container_width=True)

    with st.expander("📝 模拟原理", expanded=False):
        st.markdown(f"""
        **模拟设置：**
        - 四级供应链：零售商 → 批发商 → 分销商 → 制造商
        - 客户需求：N({mean}, {sigma}²)
        - 提前期 L = {L}
        - 安全系数 Z = {Z}（对应 95% 服务水平）
        - 预测方法：{n_MA} 期移动平均

        **订货策略（Order-up-to）：**
        $$订单量 = \\max(0, \\hat{{d}} \\times (L+1) + Z \\times \\sigma \\times \\sqrt{{L+1}} - 当前库存 - 在途订单 + 缺货)$$

        **牛鞭比：**
        牛鞭比 > 1 表示该级需求波动大于客户需求波动。比值越大说明牛鞭效应越严重。
        """)
