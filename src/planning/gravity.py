"""
重心法选址模块
==============
求解单设施最优选址的经典方法：给定多个需求点的坐标和需求量，
找一个位置使得总运输成本（加权距离之和）最小。

算法分两步：
1. 基本重心法：X = Σ(Wi×Xi)/ΣWi, Y = Σ(Wi×Yi)/ΣWi（加权平均）
2. 迭代优化：用距离倒数加权反复修正坐标，直到收敛

假设：运输成本与距离和运量成正比，使用欧氏距离（直线距离）。
"""
import streamlit as st
import pandas as pd
import math
from src.utils.stats import fmt, parse_num
from src.utils.ui import alert


SAMPLE_DATA = [
    {"name": "需求点 A", "x": 3.0, "y": 8.0, "w": 2000.0},
    {"name": "需求点 B", "x": 8.0, "y": 2.0, "w": 3000.0},
    {"name": "需求点 C", "x": 2.0, "y": 5.0, "w": 2500.0},
    {"name": "需求点 D", "x": 6.0, "y": 4.0, "w": 1000.0},
    {"name": "需求点 E", "x": 8.0, "y": 8.0, "w": 1500.0},
]


def render_gravity():
    st.markdown("## 📍 重心法选址")
    st.caption("基于重心法求解单设施最优选址。输入各需求点坐标和需求量，计算总运输成本最小的选址坐标。支持迭代优化。")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📋 需求点数据")
        df = st.data_editor(
            pd.DataFrame(SAMPLE_DATA).rename(columns={
                "name": "名称", "x": "X 坐标", "y": "Y 坐标", "w": "需求量 Wi (吨)"
            }),
            num_rows="dynamic",
            use_container_width=True,
            key="gravity_editor",
        )
        iterations = st.number_input("迭代次数", value=20, min_value=0, max_value=200, step=1, key="grav_iter")

        if st.button("计算最优选址", key="grav_calc", use_container_width=True):
            _calc_gravity(df, iterations)


def _calc_gravity(df, max_iterations):
    """重心法计算"""
    # 读取数据
    points = []
    for _, row in df.iterrows():
        name = str(row["名称"]) if pd.notna(row["名称"]) else ""
        x = row["X 坐标"] if pd.notna(row["X 坐标"]) else None
        y = row["Y 坐标"] if pd.notna(row["Y 坐标"]) else None
        w = row["需求量 Wi (吨)"] if pd.notna(row["需求量 Wi (吨)"]) else None

        if name and x is not None and y is not None and w is not None and w > 0:
            points.append({"name": name, "x": float(x), "y": float(y), "w": float(w)})

    if len(points) < 2:
        alert("请至少输入 2 个有效需求点", "error")
        return

    # 1. 基本重心法
    sum_w = sum(p["w"] for p in points)
    sum_wx = sum(p["w"] * p["x"] for p in points)
    sum_wy = sum(p["w"] * p["y"] for p in points)
    X0 = sum_wx / sum_w
    Y0 = sum_wy / sum_w

    def total_cost(cx, cy):
        return sum(p["w"] * math.sqrt((p["x"] - cx) ** 2 + (p["y"] - cy) ** 2) for p in points)

    cost0 = total_cost(X0, Y0)

    # 2. 迭代优化
    Xk, Yk = X0, Y0
    iter_history = [{"iter": 0, "x": X0, "y": Y0, "cost": cost0}]

    for k in range(1, max_iterations + 1):
        sum_wd = 0
        sum_wdx = 0
        sum_wdy = 0
        has_zero = False

        for p in points:
            d = math.sqrt((p["x"] - Xk) ** 2 + (p["y"] - Yk) ** 2)
            if d < 1e-10:
                has_zero = True
                break
            wd = p["w"] / d
            sum_wd += wd
            sum_wdx += wd * p["x"]
            sum_wdy += wd * p["y"]

        if has_zero or sum_wd == 0:
            break

        Xk = sum_wdx / sum_wd
        Yk = sum_wdy / sum_wd
        cost_k = total_cost(Xk, Yk)
        iter_history.append({"iter": k, "x": Xk, "y": Yk, "cost": cost_k})

        # 收敛判断
        prev_cost = iter_history[k - 1]["cost"]
        if abs(prev_cost - cost_k) < 1e-10:
            break
        if prev_cost > 1e-10 and abs(prev_cost - cost_k) / prev_cost < 1e-8 and k > 5:
            break

    last = iter_history[-1]
    improvement = ((cost0 - last["cost"]) / cost0 * 100) if cost0 > 0 else 0

    # 结果展示
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 📍 基本重心法")
        st.metric("X₀ 坐标", fmt(X0))
        st.metric("Y₀ 坐标", fmt(Y0))
        st.metric("初始总加权距离", f"{fmt(cost0)} 吨·单位距离")

    with col2:
        st.markdown("#### 🎯 迭代优化结果")
        st.metric("最优选址", f"({fmt(last['x'])}, {fmt(last['y'])})")
        st.metric("最优总运输成本", f"{fmt(last['cost'])} 吨·距离")
        st.metric("迭代次数", str(last["iter"]))
        st.metric("相比基本重心法", f"↓ {fmt(improvement)}%")

    # 选址散点图
    import plotly.graph_objects as go

    fig = go.Figure()
    # 需求点
    sizes = [p["w"] * 5 for p in points]
    fig.add_trace(go.Scatter(
        x=[p["x"] for p in points], y=[p["y"] for p in points],
        mode='markers+text', name='需求点',
        text=[p["name"] for p in points], textposition="top center",
        marker=dict(size=sizes, color='#2563eb', opacity=0.7),
    ))
    # 初始重心
    fig.add_trace(go.Scatter(
        x=[X0], y=[Y0], mode='markers', name='基本重心法',
        marker=dict(size=12, color='#f59e0b', symbol='x'),
    ))
    # 最优选址
    fig.add_trace(go.Scatter(
        x=[last["x"]], y=[last["y"]], mode='markers', name='最优选址',
        marker=dict(size=14, color='#ef4444', symbol='star'),
    ))
    # 连线
    for p in points:
        fig.add_trace(go.Scatter(
            x=[p["x"], last["x"]], y=[p["y"], last["y"]],
            mode='lines', showlegend=False,
            line=dict(color='#cbd5e1', dash='dot'),
        ))

    fig.update_layout(title="需求点与最优选址", xaxis_title="X 坐标", yaxis_title="Y 坐标", height=450)
    st.plotly_chart(fig, use_container_width=True)

    # 收敛曲线
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=[h["iter"] for h in iter_history],
        y=[h["cost"] for h in iter_history],
        mode='lines+markers', name='总成本',
        line=dict(color='#2563eb'),
    ))
    fig2.update_layout(title="迭代收敛曲线", xaxis_title="迭代次数", yaxis_title="总运输成本", height=300)
    st.plotly_chart(fig2, use_container_width=True)

    # 明细表
    st.markdown("#### 📋 各需求点明细")
    detail_data = []
    for p in points:
        dist = math.sqrt((p["x"] - last["x"]) ** 2 + (p["y"] - last["y"]) ** 2)
        detail_data.append({
            "需求点": p["name"],
            "坐标": f"({fmt(p['x'])}, {fmt(p['y'])})",
            "需求量(吨)": fmt(p["w"], 0),
            "到选址距离": fmt(dist),
            "加权距离": fmt(p["w"] * dist),
        })
    detail_data.append({
        "需求点": "**合计**",
        "坐标": "",
        "需求量(吨)": f"**{fmt(sum_w, 0)}**",
        "到选址距离": "",
        "加权距离": f"**{fmt(last['cost'])}**",
    })
    st.dataframe(pd.DataFrame(detail_data), use_container_width=True, hide_index=True)
