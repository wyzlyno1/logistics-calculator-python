"""ABC 分类分析模块"""
import streamlit as st
import pandas as pd
from src.utils.stats import fmt, parse_num
from src.utils.ui import alert


SAMPLE_DATA = [
    {"name": "SKU-001", "demand": 12000, "cost": 50},
    {"name": "SKU-002", "demand": 8000, "cost": 120},
    {"name": "SKU-003", "demand": 25000, "cost": 8},
    {"name": "SKU-004", "demand": 3000, "cost": 200},
    {"name": "SKU-005", "demand": 15000, "cost": 15},
    {"name": "SKU-006", "demand": 5000, "cost": 80},
    {"name": "SKU-007", "demand": 40000, "cost": 3},
    {"name": "SKU-008", "demand": 6000, "cost": 45},
    {"name": "SKU-009", "demand": 2000, "cost": 300},
    {"name": "SKU-010", "demand": 10000, "cost": 25},
    {"name": "SKU-011", "demand": 18000, "cost": 10},
    {"name": "SKU-012", "demand": 800, "cost": 500},
    {"name": "SKU-013", "demand": 22000, "cost": 6},
    {"name": "SKU-014", "demand": 9000, "cost": 35},
    {"name": "SKU-015", "demand": 1500, "cost": 150},
]


def render_abc():
    st.markdown("## 📊 ABC 分类分析")
    st.caption("按年消耗金额对库存物品进行 ABC 分类，自动绘制帕累托图。支持自定义分类阈值。")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📋 物品数据")

        # 数据编辑器
        df = st.data_editor(
            pd.DataFrame(SAMPLE_DATA).rename(columns={
                "name": "物品名称", "demand": "年需求量", "cost": "单价(元)"
            }),
            num_rows="dynamic",
            use_container_width=True,
            key="abc_editor",
        )

        st.markdown("#### ⚙️ 分类阈值")
        pct_col1, pct_col2, pct_col3 = st.columns(3)
        with pct_col1:
            a_pct = st.number_input("A 类占比%", value=70.0, min_value=0.0, max_value=100.0, step=1.0, key="abc_a")
        with pct_col2:
            b_pct = st.number_input("B 类占比%", value=20.0, min_value=0.0, max_value=100.0, step=1.0, key="abc_b")
        with pct_col3:
            c_pct = st.number_input("C 类占比%", value=100.0 - a_pct - b_pct, disabled=True, key="abc_c")

        if st.button("计算并分类", key="abc_calc", use_container_width=True):
            _calc_abc(df, a_pct, b_pct)


def _calc_abc(df, a_threshold, b_threshold):
    """ABC 分类计算"""
    # 清理数据
    items = []
    for _, row in df.iterrows():
        name = str(row["物品名称"]) if pd.notna(row["物品名称"]) else ""
        demand = row["年需求量"]
        cost = row["单价(元)"]
        if pd.notna(demand) and pd.notna(cost) and demand > 0 and cost > 0 and name:
            items.append({
                "name": name,
                "demand": float(demand),
                "cost": float(cost),
                "value": float(demand) * float(cost),
            })

    if len(items) < 3:
        alert("请至少输入 3 个有效物品（名称、需求量和单价均需填写）", "error")
        return

    # 按年消耗金额降序
    items.sort(key=lambda x: x["value"], reverse=True)
    total_value = sum(it["value"] for it in items)

    # 计算累计占比
    cum_pct = 0
    for i, it in enumerate(items):
        it["pct"] = (it["value"] / total_value) * 100
        cum_pct += it["pct"]
        it["cum_pct"] = cum_pct
        it["rank"] = i + 1

        # 分类
        if it["cum_pct"] - it["pct"] < a_threshold:
            it["cls"] = "A"
        elif it["cum_pct"] - it["pct"] < a_threshold + b_threshold:
            it["cls"] = "B"
        else:
            it["cls"] = "C"

    a_items = [it for it in items if it["cls"] == "A"]
    b_items = [it for it in items if it["cls"] == "B"]
    c_items = [it for it in items if it["cls"] == "C"]

    a_val = sum(it["value"] for it in a_items)
    b_val = sum(it["value"] for it in b_items)
    c_val = sum(it["value"] for it in c_items)

    # 结果展示
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📊 分类汇总")
        cls_cols = st.columns(3)
        with cls_cols[0]:
            st.metric("A 类", f"{len(a_items)} 种", delta=f"{fmt((a_val/total_value)*100, 1)}%")
            st.caption(f"金额：{fmt(a_val)} 元")
        with cls_cols[1]:
            st.metric("B 类", f"{len(b_items)} 种", delta=f"{fmt((b_val/total_value)*100, 1)}%")
            st.caption(f"金额：{fmt(b_val)} 元")
        with cls_cols[2]:
            st.metric("C 类", f"{len(c_items)} 种", delta=f"{fmt((c_val/total_value)*100, 1)}%")
            st.caption(f"金额：{fmt(c_val)} 元")

    with col2:
        # 帕累托图
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        names = [it["name"] for it in items]
        values = [it["value"] for it in items]
        cum_pcts = [it["cum_pct"] for it in items]
        colors = ["#ef4444" if it["cls"] == "A" else "#f59e0b" if it["cls"] == "B" else "#10b981" for it in items]

        fig.add_trace(
            go.Bar(x=names, y=values, name="年消耗金额", marker_color=colors),
            secondary_y=False,
        )
        fig.add_trace(
            go.Scatter(x=names, y=cum_pcts, mode='lines+markers', name="累计占比%",
                       line=dict(color='#2563eb', width=2.5)),
            secondary_y=True,
        )
        fig.add_hline(y=a_threshold, line_dash="dash", line_color="gray",
                      annotation_text=f"A类阈值 {a_threshold}%", secondary_y=True)
        fig.add_hline(y=a_threshold + b_threshold, line_dash="dash", line_color="gray",
                      annotation_text=f"B类阈值 {a_threshold+b_threshold}%", secondary_y=True)

        fig.update_layout(title="帕累托图", height=400, hovermode="x unified")
        fig.update_xaxes(title="物品")
        fig.update_yaxes(title="年消耗金额 (元)", secondary_y=False)
        fig.update_yaxes(title="累计占比 (%)", secondary_y=True, range=[0, 105])
        st.plotly_chart(fig, use_container_width=True)

    # 明细表
    st.markdown("#### 📋 物品排名明细")
    detail_df = pd.DataFrame([
        {
            "排名": it["rank"],
            "名称": it["name"],
            "年需求量": fmt(it["demand"], 0),
            "单价": fmt(it["cost"]),
            "年消耗金额": fmt(it["value"]),
            "占比": f"{fmt(it['pct'], 1)}%",
            "累计占比": f"{fmt(it['cum_pct'], 1)}%",
            "分类": it["cls"],
        }
        for it in items
    ])
    st.dataframe(detail_df, use_container_width=True, hide_index=True)
