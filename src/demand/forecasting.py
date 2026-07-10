"""
需求预测方法模块
================
三种时间序列预测方法，用于从历史数据推算未来需求：

1. 简单移动平均 — 取最近 n 期的平均值
   适合：需求平稳、无明显趋势

2. 加权移动平均 — 近期数据权重更大（如 0.5, 0.3, 0.2）
   适合：近期趋势更重要

3. 一次指数平滑 — 所有历史数据加权，权重指数衰减
   公式：Ft+1 = α×Dt + (1-α)×Ft
   α 越大 → 越敏感于近期变化；α 越小 → 越平滑

误差指标：MAD（平均绝对偏差）、MSE（均方误差）、MAPE（平均绝对百分比误差）
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from src.utils.stats import fmt, parse_num
from src.utils.ui import alert


SAMPLE_DATA = "120, 135, 128, 142, 138, 150, 145, 158, 152, 165, 160, 172"


def render_forecasting():
    st.markdown("## 📈 需求预测方法")
    st.caption("多种时间序列预测方法，含 MAD/MSE/MAPE 误差分析。输入历史数据，输出预测值和精度评估。")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("#### 📋 历史数据")
        st.caption("每行一个值，或逗号/空格分隔")
        data_text = st.text_area("历史数据", value=SAMPLE_DATA, height=100, key="fc_data")
        periods = st.number_input("预测期数（未来多少期）", value=3, min_value=1, max_value=20, step=1,
                                  key="fc_periods")

    # 方法选择
    tab1, tab2, tab3 = st.tabs(["移动平均法", "加权移动平均", "一次指数平滑"])

    with tab1:
        _render_ma(data_text, periods)
    with tab2:
        _render_wma(data_text, periods)
    with tab3:
        _render_ses(data_text, periods)


def _read_data(data_text):
    """解析历史数据"""
    text = data_text.replace(',', ' ').replace('，', ' ').replace('\n', ' ')
    parts = text.split()
    return [parse_num(p) for p in parts if p.strip() and not np.isnan(parse_num(p))]


def _calc_errors(actual, forecast):
    """计算预测误差指标"""
    valid = [(a, f) for a, f in zip(actual, forecast) if f is not None and a != 0]
    if not valid:
        return None

    n = len(valid)
    MAD = sum(abs(a - f) for a, f in valid) / n
    MSE = sum((a - f) ** 2 for a, f in valid) / n
    MAPE = sum(abs((a - f) / a) for a, f in valid) / n * 100

    return {"MAD": MAD, "MSE": MSE, "MAPE": MAPE, "RMSE": np.sqrt(MSE)}


def _display_results(data, forecasts, method_name, future_forecasts, periods):
    """统一的结果展示"""
    n = len(data)

    # 误差评估
    aligned_forecast = forecasts[:n]
    errors = _calc_errors(data, aligned_forecast)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 📏 误差评估")
        if errors:
            metric_cols = st.columns(4)
            with metric_cols[0]:
                st.metric("MAD", f"{fmt(errors['MAD'], 2)}")
            with metric_cols[1]:
                st.metric("MSE", f"{fmt(errors['MSE'], 2)}")
            with metric_cols[2]:
                st.metric("MAPE", f"{fmt(errors['MAPE'], 2)}%")
            with metric_cols[3]:
                st.metric("RMSE", f"{fmt(errors['RMSE'], 2)}")

            if errors["MAPE"] < 10:
                alert(f"MAPE = {fmt(errors['MAPE'], 1)}% → 高精度", "success")
            elif errors["MAPE"] < 20:
                alert(f"MAPE = {fmt(errors['MAPE'], 1)}% → 良好", "info")
            elif errors["MAPE"] < 50:
                alert(f"MAPE = {fmt(errors['MAPE'], 1)}% → 一般", "warning")
            else:
                alert(f"MAPE = {fmt(errors['MAPE'], 1)}% → 差", "error")

    with col2:
        # 预测图表
        fig = go.Figure()
        t_actual = list(range(1, n + 1))
        fig.add_trace(go.Scatter(x=t_actual, y=data, mode='lines+markers',
                                 name='实际值', line=dict(color='#475569', width=2)))

        # 拟合值
        fit_y = [f for f in forecasts if f is not None]
        fit_x = list(range(n - len(fit_y) + 1, n + 1))
        if fit_x and fit_y:
            fig.add_trace(go.Scatter(x=fit_x, y=fit_y, mode='lines+markers',
                                     name='拟合值', line=dict(color='#2563eb', dash='dash')))

        # 未来预测
        if future_forecasts:
            future_x = list(range(n + 1, n + len(future_forecasts) + 1))
            fig.add_trace(go.Scatter(x=future_x, y=future_forecasts, mode='lines+markers',
                                     name='未来预测', line=dict(color='#ef4444', width=2.5)))

        fig.update_layout(title=f"预测结果 — {method_name}",
                          xaxis_title="时期", yaxis_title="值", height=350,
                          hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

    # 未来预测
    if future_forecasts:
        st.markdown("#### 📊 未来预测")
        future_cols = st.columns(periods)
        for i, (col, fc) in enumerate(zip(future_cols, future_forecasts)):
            with col:
                st.metric(f"第 {n+i+1} 期", fmt(fc, 2))

    # 详细数据表
    st.markdown("#### 📋 预测对照表")
    table_data = []
    for t in range(n):
        fc_val = forecasts[t] if t < len(forecasts) and forecasts[t] is not None else None
        abs_err = abs(data[t] - fc_val) if fc_val is not None else None
        table_data.append({
            "时期": t + 1,
            "实际值": fmt(data[t], 1),
            "预测值": fmt(fc_val, 2) if fc_val is not None else "—",
            "绝对误差": fmt(abs_err, 2) if abs_err is not None else "—",
        })
    for f_idx, fc in enumerate(future_forecasts):
        table_data.append({
            "时期": n + f_idx + 1,
            "实际值": "（未来）",
            "预测值": f"**{fmt(fc, 2)}**",
            "绝对误差": "—",
        })
    st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)


def _render_ma(data_text, periods):
    """移动平均法"""
    n_ma = st.number_input("移动平均期数 n", value=3, min_value=2, max_value=20, step=1, key="fc_ma_n")

    if st.button("计算预测", key="fc_ma_calc", use_container_width=True):
        data = _read_data(data_text)
        if len(data) < n_ma + 1:
            alert(f"至少需要 {n_ma + 1} 期历史数据", "error")
            return

        forecasts = []
        for t in range(len(data)):
            if t < n_ma:
                forecasts.append(None)
            else:
                forecasts.append(np.mean(data[t - n_ma:t]))

        # 未来预测（滚动）
        last_n = data[-n_ma:].copy()
        future = []
        for _ in range(periods):
            fc = np.mean(last_n)
            future.append(fc)
            last_n.pop(0)
            last_n.append(fc)

        _display_results(data, forecasts, f"移动平均法 (n={n_ma})", future, periods)


def _render_wma(data_text, periods):
    """加权移动平均"""
    col_a, col_b = st.columns(2)
    with col_a:
        n_wma = st.number_input("移动期数 n", value=3, min_value=2, max_value=10, step=1, key="fc_wma_n")
    with col_b:
        weights_text = st.text_input("权重（逗号分隔，从最近到最远）", value="0.5, 0.3, 0.2",
                                     key="fc_wma_weights")

    if st.button("计算预测", key="fc_wma_calc", use_container_width=True):
        data = _read_data(data_text)
        weights = [parse_num(w) for w in weights_text.replace(',', ' ').split() if w.strip()]
        weights = [w for w in weights if not np.isnan(w)]

        if len(weights) != n_wma:
            alert(f"权重数量 ({len(weights)}) 与移动期数 ({n_wma}) 不匹配", "error")
            return

        w_sum = sum(weights)
        if abs(w_sum - 1) > 0.01:
            alert(f"权重之和为 {fmt(w_sum)}，不等于 1。将自动归一化。", "warning")
            weights = [w / w_sum for w in weights]

        if len(data) < n_wma + 1:
            alert(f"至少需要 {n_wma + 1} 期数据", "error")
            return

        forecasts = []
        for t in range(len(data)):
            if t < n_wma:
                forecasts.append(None)
            else:
                fc = sum(weights[j] * data[t - 1 - j] for j in range(n_wma))
                forecasts.append(fc)

        # 未来预测
        buf = list(reversed(data[-n_wma:]))
        future = []
        for _ in range(periods):
            fc = sum(weights[j] * buf[j] for j in range(n_wma))
            future.append(fc)
            buf.insert(0, fc)
            buf.pop()

        _display_results(data, forecasts, f"加权移动平均 (n={n_wma})", future, periods)


def _render_ses(data_text, periods):
    """一次指数平滑"""
    alpha = st.number_input("平滑系数 α", value=0.3, min_value=0.01, max_value=0.99, step=0.01,
                            key="fc_ses_alpha")

    if st.button("计算预测", key="fc_ses_calc", use_container_width=True):
        data = _read_data(data_text)

        if len(data) < 3:
            alert("至少需要 3 期历史数据", "error")
            return

        # 初始值 = 第一期实际值
        F0 = data[0]
        Ft = F0

        forecasts = [None]  # 第一期无预测
        for t in range(len(data)):
            next_ft = alpha * data[t] + (1 - alpha) * Ft
            forecasts.append(next_ft)
            Ft = next_ft

        # 对齐：forecasts[t] 是 t 期的预测值
        aligned = []
        for t in range(len(data)):
            if t == 0:
                aligned.append(None)
            else:
                aligned.append(forecasts[t])

        # 未来预测（SES 对所有未来期预测相同）
        last_f = forecasts[-1]
        future = [last_f] * periods

        _display_results(data, aligned, f"一次指数平滑 (α={alpha})", future, periods)
