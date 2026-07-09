"""选址案例分析 — 因素评分法 + 盈亏平衡法"""
import streamlit as st
import pandas as pd
import math
from src.utils.stats import fmt, parse_num
from src.utils.ui import alert


def render_location():
    st.markdown("## 🏢 选址案例分析")
    st.caption("综合选址决策工具。因素评分法对多个备选地址进行加权打分排序，盈亏平衡法基于成本结构对比最优选址。")

    tab1, tab2 = st.tabs(["因素评分法", "盈亏平衡法"])

    with tab1:
        _render_factor_method()
    with tab2:
        _render_breakeven_method()


def _render_factor_method():
    """因素评分法"""
    st.markdown("### 因素评分法")

    col1, col2 = st.columns([1, 2])
    with col1:
        n_locations = st.number_input("备选地址数", value=3, min_value=2, max_value=8, step=1, key="lf_nloc")
        n_factors = st.number_input("评分因素数", value=5, min_value=2, max_value=10, step=1, key="lf_nfac")

        # 因素名称和权重
        st.markdown("#### 评分因素与权重")
        factors = []
        weights = []
        for j in range(n_factors):
            fj1, fj2 = st.columns([2, 1])
            with fj1:
                name = st.text_input(f"因素{j+1}名称", value=["交通便利性", "劳动力成本", "地价", "市场接近度", "政策优惠"][j] if j < 5 else f"因素{j+1}", key=f"lf_fname_{j}")
            with fj2:
                w = st.number_input(f"权重", value=[0.25, 0.20, 0.15, 0.25, 0.15][j] if j < 5 else 0.10, min_value=0.0, max_value=1.0, step=0.01, key=f"lf_fw_{j}")
            factors.append(name)
            weights.append(w)

        # 评分矩阵
        st.markdown("#### 评分矩阵")
        loc_names = []
        scores = []
        for i in range(n_locations):
            st.markdown(f"**地址 {i+1}**")
            name = st.text_input(f"名称", value=chr(65+i), key=f"lf_lname_{i}")
            loc_names.append(name)
            row_scores = []
            score_cols = st.columns(n_factors)
            for j in range(n_factors):
                with score_cols[j]:
                    s = st.number_input(
                        f"{factors[j]}", value=float([
                            [85, 70, 60, 90, 75],
                            [75, 80, 75, 70, 80],
                            [65, 90, 85, 60, 65],
                        ][i][j] if i < 3 and j < 5 else 70),
                        min_value=0.0, max_value=100.0, step=1.0,
                        key=f"lf_score_{i}_{j}",
                        label_visibility="visible",
                    )
                    row_scores.append(s)
            scores.append(row_scores)

        if st.button("计算评分", key="lf_calc", use_container_width=True):
            _calc_factor(factors, weights, loc_names, scores)


def _calc_factor(factors, weights, loc_names, scores):
    """因素评分法计算"""
    n_factors = len(factors)
    n_locations = len(loc_names)

    # 权重归一化
    weight_sum = sum(weights)
    if abs(weight_sum) < 1e-10:
        alert("请至少为一个因素设置权重大于 0", "error")
        return
    if abs(weight_sum - 1) > 0.02:
        alert(f"权重之和为 {fmt(weight_sum)}，不等于 1。将自动归一化。", "warning")
    weights = [w / weight_sum for w in weights]

    # 计算加权总分
    totals = []
    for i in range(n_locations):
        total = sum(scores[i][j] * weights[j] for j in range(n_factors))
        totals.append({"name": loc_names[i], "index": i, "total": total})

    totals.sort(key=lambda t: t["total"], reverse=True)

    # 结果
    st.markdown("#### 🏆 因素评分法结果")
    st.metric("最优选址", f"{totals[0]['name']}", delta=f"得分：{fmt(totals[0]['total'], 1)}")

    rank_cols = st.columns(n_locations)
    for rank, t in enumerate(totals):
        with rank_cols[rank]:
            st.metric(f"第{rank+1}名", t["name"], delta=f"{fmt(t['total'], 1)} 分")

    # 评分明细表
    st.markdown("#### 📋 评分明细")
    detail = {"因素 (权重)": [f"{factors[j]} ({fmt(weights[j]*100, 0)}%)" for j in range(n_factors)]}
    for i in range(n_locations):
        detail[loc_names[i]] = [fmt(scores[i][j], 0) for j in range(n_factors)]

    # 加总分行
    detail["因素 (权重)"].append("**加权总分**")
    for i in range(n_locations):
        t = next(t for t in totals if t["index"] == i)
        detail[loc_names[i]].append(f"**{fmt(t['total'], 1)}**")

    st.dataframe(pd.DataFrame(detail), use_container_width=True, hide_index=True)

    # 柱状图
    import plotly.graph_objects as go
    fig = go.Figure(data=[
        go.Bar(x=[t["name"] for t in totals], y=[t["total"] for t in totals],
               text=[fmt(t["total"], 1) for t in totals], textposition='outside',
               marker_color=['#2563eb' if i == 0 else '#94a3b8' for i in range(len(totals))])
    ])
    fig.update_layout(title="各地址加权总分", yaxis_title="得分", height=350)
    st.plotly_chart(fig, use_container_width=True)


def _render_breakeven_method():
    """盈亏平衡法"""
    st.markdown("### 盈亏平衡法")

    col1, col2 = st.columns(2)
    with col1:
        Q = st.number_input("预期年产量 Q (件/年)", value=10000.0, step=100.0, key="lb_Q")
        st.caption("每个备选地址的成本结构（格式：名称, 年固定成本, 单位变动成本）")
        data_text = st.text_area(
            "成本数据",
            value="地址A, 500000, 25\n地址B, 350000, 40\n地址C, 200000, 55",
            height=120,
            key="lb_data",
        )

        if st.button("计算", key="lb_calc", use_container_width=True):
            _calc_breakeven(Q, data_text)


def _calc_breakeven(Q, data_text):
    """盈亏平衡法计算"""
    if Q <= 0:
        alert("请填写预期年产量 Q", "error")
        return

    locations = []
    for line in data_text.strip().split('\n'):
        parts = line.replace(',', ' ').replace('，', ' ').split()
        if len(parts) >= 3:
            name = parts[0]
            fc = parse_num(parts[1])
            vc = parse_num(parts[2])
            if name and not math.isnan(fc) and not math.isnan(vc):
                locations.append({"name": name, "fc": fc, "vc": vc})

    if len(locations) < 2:
        alert("请至少输入两个有效地址", "error")
        return

    # 计算各地址在 Q 下的总成本
    for loc in locations:
        loc["tc"] = loc["fc"] + loc["vc"] * Q
    locations.sort(key=lambda l: l["tc"])
    best = locations[0]

    # 两两盈亏平衡点
    breakpoints = []
    for i in range(len(locations)):
        for j in range(i + 1, len(locations)):
            a = locations[i]
            b = locations[j]
            if abs(a["vc"] - b["vc"]) > 1e-10:
                q_be = (b["fc"] - a["fc"]) / (a["vc"] - b["vc"])
                if q_be > 0:
                    breakpoints.append({"q": q_be, "a": a["name"], "b": b["name"]})
    breakpoints.sort(key=lambda x: x["q"])

    # 结果
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 💰 盈亏平衡法结果")
        st.metric("最优选址", best["name"], delta=f"年总成本：{fmt(best['tc'], 0)} 元")

        rank_cols = st.columns(len(locations))
        for i, loc in enumerate(locations):
            with rank_cols[i]:
                icon = "🥇" if i == 0 else "🥈" if i == 1 else "🥉"
                st.metric(f"{icon} {loc['name']}", f"{fmt(loc['tc'], 0)} 元")
                st.caption(f"固定 {fmt(loc['fc'], 0)} + 变动 {fmt(loc['vc'])}×{fmt(Q, 0)}")

    # 盈亏平衡点
    if breakpoints:
        with col2:
            st.markdown("#### ⚖️ 盈亏平衡点")
            bp_df = pd.DataFrame([
                {"地址对": f"{bp['a']} ↔ {bp['b']}", "平衡点产量": f"{fmt(bp['q'], 0)} 件"}
                for bp in breakpoints
            ])
            st.dataframe(bp_df, use_container_width=True, hide_index=True)

    # 成本对比图
    import plotly.graph_objects as go
    import numpy as np

    q_max = Q * 1.5
    fig = go.Figure()
    colors = ['#2563eb', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6']
    for i, loc in enumerate(locations):
        q_range = np.linspace(0, q_max, 200)
        tc_line = loc["fc"] + loc["vc"] * q_range
        fig.add_trace(go.Scatter(
            x=q_range, y=tc_line, mode='lines',
            name=f'{loc["name"]} (TC={fmt(loc["fc"], 0)}+{fmt(loc["vc"])}Q)',
            line=dict(color=colors[i % len(colors)], width=2),
        ))
        # Q 处的点
        fig.add_trace(go.Scatter(
            x=[Q], y=[loc["tc"]], mode='markers',
            name=f'{loc["name"]} at Q={fmt(Q, 0)}',
            marker=dict(size=10, color=colors[i % len(colors)]),
            showlegend=False,
        ))

    fig.add_vline(x=Q, line_dash="dash", line_color="gray", annotation_text=f"Q={fmt(Q, 0)}")
    fig.update_layout(title="成本对比图", xaxis_title="产量 (件)", yaxis_title="年总成本 (元)", height=400,
                      hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)
