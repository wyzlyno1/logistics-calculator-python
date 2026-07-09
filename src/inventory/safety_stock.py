"""安全库存计算模块"""
import streamlit as st
import math
from src.utils.stats import fmt, get_z_value, COMMON_SERVICE_LEVELS
from src.utils.ui import result_grid, alert


def render_safety_stock():
    st.markdown("## 🛡️ 安全库存计算")
    st.caption("根据需求分布和服务水平计算安全库存量与再订货点。支持三种模型。")

    # Z 值参考表
    with st.expander("📋 常用服务水平 Z 值参考", expanded=False):
        from src.utils.stats import Z_TABLE
        items = sorted(Z_TABLE.items())
        cols = st.columns(4)
        for i, (sl, z) in enumerate(items):
            with cols[i % 4]:
                st.caption(f"{sl:.1f}% → Z = {z:.3f}")

    tab1, tab2, tab3 = st.tabs(["需求不确定", "提前期不确定", "两者均不确定"])

    with tab1:
        _render_demand_model()
    with tab2:
        _render_leadtime_model()
    with tab3:
        _render_both_model()


def _service_level_selector(prefix: str):
    """服务水平选择器，返回 Z 值和选中的服务水平"""
    sl_options = [f"{sl}%" for sl in COMMON_SERVICE_LEVELS] + ["自定义 Z 值"]
    sl_choice = st.selectbox("服务水平", sl_options, index=1, key=f"{prefix}_sl")

    if sl_choice == "自定义 Z 值":
        Z = st.number_input("Z 值", value=1.645, step=0.01, key=f"{prefix}_Z_custom")
        sl_display = "自定义"
    else:
        sl_val = float(sl_choice.replace('%', ''))
        Z = get_z_value(sl_val)
        sl_display = sl_choice

    st.caption(f"当前 Z 值：**{fmt(Z, 4)}**")
    return Z, sl_display


def _render_demand_model():
    """模型1：需求不确定"""
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 📋 输入参数 — 需求不确定模型")
        d_avg = st.number_input("平均日需求量 d̄ (件/天)", value=50.0, step=1.0, key="ss1_d")
        sigma_d = st.number_input("日需求标准差 σd (件/天)", value=10.0, step=1.0, min_value=0.0, key="ss1_sigma")
        L = st.number_input("提前期 L (天)", value=7.0, step=1.0, key="ss1_L")
        Z, sl_display = _service_level_selector("ss1")

        if st.button("计算", key="ss1_calc", use_container_width=True):
            if d_avg <= 0 or sigma_d < 0 or L <= 0:
                alert("参数不合法", "error")
            elif Z is None:
                alert("请选择有效的服务水平", "error")
            else:
                sigma_L = sigma_d * math.sqrt(L)
                SS = Z * sigma_L
                ROP = d_avg * L + SS
                avg_demand_L = d_avg * L

                with col2:
                    st.markdown("#### 📊 计算结果")
                    st.metric("安全库存 SS", f"{fmt(SS)} 件")
                    result_grid([
                        {"label": "再订货点 ROP", "value": fmt(ROP), "unit": "件"},
                        {"label": "提前期内平均需求", "value": fmt(avg_demand_L), "unit": "件"},
                        {"label": "提前期内需求标准差 σL", "value": fmt(sigma_L), "unit": "件"},
                        {"label": f"Z 值（服务水平 {sl_display}）", "value": fmt(Z, 4), "unit": ""},
                    ])

                with st.expander("📝 计算步骤", expanded=False):
                    st.markdown(f"""
                    **1. 确定 Z 值**：服务水平 = {sl_display} → Z = **{fmt(Z, 4)}**

                    **2. 计算提前期内需求标准差 σL**
                    $$\\sigma_L = \\sigma_d \\times \\sqrt{{L}} = {fmt(sigma_d)} \\times \\sqrt{{{fmt(L, 0)}}} = {fmt(sigma_d)} \\times {fmt(math.sqrt(L))} = \\textbf{{{fmt(sigma_L)} 件}}$$

                    **3. 计算安全库存 SS**
                    $$SS = Z \\times \\sigma_L = {fmt(Z, 4)} \\times {fmt(sigma_L)} = \\textbf{{{fmt(SS)} 件}}$$

                    **4. 计算再订货点 ROP**
                    $$ROP = \\bar{{d}} \\times L + SS = {fmt(d_avg)} \\times {fmt(L, 0)} + {fmt(SS)} = \\textbf{{{fmt(ROP)} 件}}$$
                    """)


def _render_leadtime_model():
    """模型2：提前期不确定"""
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 📋 输入参数 — 提前期不确定模型")
        d_avg = st.number_input("平均日需求量 d̄ (件/天，确定值)", value=50.0, step=1.0, key="ss2_d")
        L_avg = st.number_input("平均提前期 L̄ (天)", value=7.0, step=1.0, key="ss2_L")
        sigma_L = st.number_input("提前期标准差 σL (天)", value=2.0, step=0.5, min_value=0.0, key="ss2_sigmaL")
        Z, sl_display = _service_level_selector("ss2")

        if st.button("计算", key="ss2_calc", use_container_width=True):
            if d_avg <= 0 or L_avg <= 0 or sigma_L < 0:
                alert("参数不合法", "error")
            elif Z is None:
                alert("请选择有效的服务水平", "error")
            else:
                SS = Z * d_avg * sigma_L
                ROP = d_avg * L_avg + SS

                with col2:
                    st.markdown("#### 📊 计算结果")
                    st.metric("安全库存 SS", f"{fmt(SS)} 件")
                    result_grid([
                        {"label": "再订货点 ROP", "value": fmt(ROP), "unit": "件"},
                        {"label": "提前期内平均需求", "value": fmt(d_avg * L_avg), "unit": "件"},
                        {"label": "需求标准差（来自提前期变异）", "value": fmt(d_avg * sigma_L), "unit": "件"},
                    ])

                with st.expander("📝 计算步骤", expanded=False):
                    st.markdown(f"""
                    $$SS = Z \\times \\bar{{d}} \\times \\sigma_L = {fmt(Z, 4)} \\times {fmt(d_avg)} \\times {fmt(sigma_L)} = \\textbf{{{fmt(SS)} 件}}$$
                    $$ROP = \\bar{{d}} \\times \\bar{{L}} + SS = \\textbf{{{fmt(ROP)} 件}}$$
                    """)


def _render_both_model():
    """模型3：两者均不确定"""
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 📋 输入参数 — 综合模型")
        d_avg = st.number_input("平均日需求量 d̄ (件/天)", value=50.0, step=1.0, key="ss3_d")
        sigma_d = st.number_input("日需求标准差 σd (件/天)", value=10.0, step=1.0, min_value=0.0, key="ss3_sigma")
        L_avg = st.number_input("平均提前期 L̄ (天)", value=7.0, step=1.0, key="ss3_L")
        sigma_L = st.number_input("提前期标准差 σL (天)", value=2.0, step=0.5, min_value=0.0, key="ss3_sigmaL")
        Z, sl_display = _service_level_selector("ss3")

        if st.button("计算", key="ss3_calc", use_container_width=True):
            if d_avg <= 0 or sigma_d < 0 or L_avg <= 0 or sigma_L < 0:
                alert("参数不合法", "error")
            elif Z is None:
                alert("请选择有效的服务水平", "error")
            else:
                sigma_combined = math.sqrt(L_avg * sigma_d ** 2 + d_avg ** 2 * sigma_L ** 2)
                SS = Z * sigma_combined
                ROP = d_avg * L_avg + SS

                with col2:
                    st.markdown("#### 📊 计算结果")
                    st.metric("安全库存 SS", f"{fmt(SS)} 件")
                    result_grid([
                        {"label": "再订货点 ROP", "value": fmt(ROP), "unit": "件"},
                        {"label": "提前期内平均需求", "value": fmt(d_avg * L_avg), "unit": "件"},
                        {"label": "综合标准差 σc", "value": fmt(sigma_combined), "unit": "件"},
                    ])

                with st.expander("📝 计算步骤", expanded=False):
                    st.markdown(f"""
                    **1. 计算综合标准差**
                    $$\\sigma_c = \\sqrt{{\\bar{{L}} \\cdot \\sigma_d^2 + \\bar{{d}}^2 \\cdot \\sigma_L^2}} = \\textbf{{{fmt(sigma_combined)} 件}}$$

                    **2. 计算安全库存**
                    $$SS = Z \\times \\sigma_c = \\textbf{{{fmt(SS)} 件}}$$

                    **3. 计算再订货点**
                    $$ROP = \\bar{{d}} \\times \\bar{{L}} + SS = \\textbf{{{fmt(ROP)} 件}}$$
                    """)
