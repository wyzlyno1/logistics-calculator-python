"""物流网络优化 — Dijkstra, Prim, Ford-Fulkerson"""
import streamlit as st
import pandas as pd
import math
import networkx as nx
import plotly.graph_objects as go
from src.utils.stats import fmt, parse_num
from src.utils.ui import alert


SAMPLE_EDGES = [
    ("A", "B", 4), ("A", "C", 2), ("B", "C", 5),
    ("B", "D", 10), ("C", "E", 3), ("E", "D", 4),
    ("D", "F", 11), ("E", "F", 8),
]


def render_network():
    st.markdown("## 🕸️ 物流网络优化")
    st.caption("图论算法可视化。输入节点和边，运行 Dijkstra 最短路径、Prim 最小生成树、Ford-Fulkerson 最大流算法。")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("#### 🔧 图数据")

        # 节点和边管理
        edges_text = st.text_area(
            "边列表（每行：起点, 终点, 权值）",
            value="\n".join(f"{s}, {t}, {w}" for s, t, w in SAMPLE_EDGES),
            height=180,
            key="net_edges",
        )
        st.caption("节点会自动从边中识别")

        # 算法选择
        algo = st.selectbox("选择算法", ["Dijkstra 最短路径", "Prim 最小生成树", "Ford-Fulkerson 最大流"],
                            key="net_algo")

        if algo == "Dijkstra 最短路径":
            nodes = _extract_nodes(edges_text)
            node_list = sorted(nodes) if nodes else ["A", "B"]
            start_node = st.selectbox("起点", node_list, key="net_d_start")
            end_node = st.selectbox("终点", node_list, index=min(1, len(node_list) - 1),
                                    key="net_d_end")
        elif algo == "Prim 最小生成树":
            st.caption("从所有节点出发，找连接全部节点的最小总权边集。")
        else:
            nodes = _extract_nodes(edges_text)
            node_list = sorted(nodes) if nodes else ["A", "B"]
            source_node = st.selectbox("源点 Source", node_list, key="net_mf_s")
            sink_node = st.selectbox("汇点 Sink", node_list, index=min(1, len(node_list) - 1),
                                     key="net_mf_t")

        if st.button("运行算法", key="net_run", use_container_width=True):
            _run_network_algo(edges_text, algo)


def _extract_nodes(edges_text):
    """从边列表提取节点"""
    nodes = set()
    for line in edges_text.strip().split('\n'):
        parts = line.replace(',', ' ').replace('，', ' ').split()
        if len(parts) >= 2:
            nodes.add(parts[0])
            nodes.add(parts[1])
    return nodes


def _parse_edges(edges_text):
    """解析边列表"""
    edges = []
    for line in edges_text.strip().split('\n'):
        parts = line.replace(',', ' ').replace('，', ' ').split()
        if len(parts) >= 3:
            from_n = parts[0]
            to_n = parts[1]
            w = parse_num(parts[2])
            if from_n and to_n and not math.isnan(w):
                edges.append((from_n, to_n, w))
    return edges


def _build_graph(edges, directed=False):
    """构建 NetworkX 图"""
    if directed:
        G = nx.DiGraph()
    else:
        G = nx.Graph()
    for u, v, w in edges:
        G.add_edge(u, v, weight=w)
    return G


def _draw_network(G, highlighted_edges=None, node_colors=None, title="网络图"):
    """用 Plotly 绘制网络图"""
    pos = nx.spring_layout(G, seed=42, k=2)

    edge_x, edge_y = [], []
    edge_traces = []
    node_x, node_y = [], []
    node_text = []

    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(node)

    # 普通边
    normal_edge_x, normal_edge_y = [], []
    hl_edge_x, hl_edge_y = [], []
    hl_set = set()
    if highlighted_edges:
        hl_set = {(u, v) for u, v in highlighted_edges}
        hl_set.update({(v, u) for u, v in highlighted_edges})

    for u, v in G.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        if (u, v) in hl_set or (v, u) in hl_set:
            hl_edge_x.extend([x0, x1, None])
            hl_edge_y.extend([y0, y1, None])
        else:
            normal_edge_x.extend([x0, x1, None])
            normal_edge_y.extend([y0, y1, None])

    fig = go.Figure()

    # 普通边
    if normal_edge_x:
        fig.add_trace(go.Scatter(
            x=normal_edge_x, y=normal_edge_y,
            mode='lines', name='边',
            line=dict(color='#cbd5e1', width=1.5),
            hoverinfo='none',
        ))

    # 高亮边
    if hl_edge_x:
        fig.add_trace(go.Scatter(
            x=hl_edge_x, y=hl_edge_y,
            mode='lines', name='结果路径',
            line=dict(color='#2563eb', width=3),
            hoverinfo='none',
        ))

    # 边标签
    for u, v, d in G.edges(data=True):
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        w = d.get('weight', '')
        is_hl = (u, v) in hl_set or (v, u) in hl_set
        fig.add_annotation(
            x=(x0 + x1) / 2, y=(y0 + y1) / 2,
            text=str(w),
            showarrow=False,
            font=dict(size=11, color='#2563eb' if is_hl else '#64748b'),
        )

    # 节点
    colors = []
    for node in G.nodes():
        if node_colors and node in node_colors:
            colors.append(node_colors[node])
        else:
            colors.append('#2563eb')

    fig.add_trace(go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=node_text,
        textposition="middle center",
        textfont=dict(color='white', size=14, family='Arial, bold'),
        marker=dict(size=30, color=colors, line=dict(width=2, color='white')),
        hoverinfo='text',
        name='节点',
    ))

    fig.update_layout(
        title=title,
        showlegend=False,
        height=400,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        margin=dict(l=10, r=10, t=40, b=10),
    )
    return fig


def _run_network_algo(edges_text, algo):
    """运行选中的算法"""
    edges = _parse_edges(edges_text)
    if len(edges) < 1:
        alert("至少需要 1 条边", "error")
        return

    nodes = _extract_nodes(edges_text)
    if len(nodes) < 2:
        alert("至少需要 2 个节点", "error")
        return

    if algo == "Dijkstra 最短路径":
        _run_dijkstra(edges)
    elif algo == "Prim 最小生成树":
        _run_prim(edges)
    else:
        _run_maxflow(edges)


def _run_dijkstra(edges):
    """Dijkstra 最短路径"""
    start = st.session_state.get("net_d_start", "A")
    end = st.session_state.get("net_d_end", "B")

    G = _build_graph(edges)

    if start not in G or end not in G:
        alert("起点或终点不在图中", "error")
        return

    if start == end:
        alert("起点和终点不能相同", "error")
        return

    try:
        path = nx.shortest_path(G, source=start, target=end, weight='weight')
        dist = nx.shortest_path_length(G, source=start, target=end, weight='weight')
    except nx.NetworkXNoPath:
        alert(f"从 {start} 无法到达 {end}", "error")
        return

    path_edges = list(zip(path[:-1], path[1:]))
    node_colors = {start: '#10b981', end: '#ef4444'}

    fig = _draw_network(G, highlighted_edges=path_edges, node_colors=node_colors,
                        title=f"Dijkstra: {start} → {end}")
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 🛣️ 最短路径结果")
        st.metric("最短距离", fmt(dist, 0))
        st.markdown(f"**路径**：{' → '.join(f'**{n}**' for n in path)}")

    with col2:
        # 各节点最短距离表
        lengths = nx.single_source_dijkstra_path_length(G, start, weight='weight')
        df = pd.DataFrame([
            {"节点": n, "最短距离": fmt(d, 0) if d != float('inf') else "∞"}
            for n, d in sorted(lengths.items(), key=lambda x: x[1] if x[1] != float('inf') else 1e99)
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)


def _run_prim(edges):
    """Prim 最小生成树"""
    G = _build_graph(edges)

    if not nx.is_connected(G):
        alert("图不连通，无法生成最小生成树", "error")
        return

    mst = nx.minimum_spanning_tree(G, weight='weight')
    mst_edges = list(mst.edges())
    total_weight = sum(d['weight'] for _, _, d in mst.edges(data=True))

    fig = _draw_network(G, highlighted_edges=mst_edges, title=f"Prim MST (总权值={fmt(total_weight, 0)})")
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 🌲 最小生成树")
        st.metric("总权值", fmt(total_weight, 0))
        st.caption(f"包含 {len(G.nodes())} 个节点，{len(mst_edges)} 条边")

    with col2:
        df = pd.DataFrame([
            {"边": f"{u} — {v}", "权值": fmt(d['weight'], 0)}
            for u, v, d in mst.edges(data=True)
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)


def _run_maxflow(edges):
    """Ford-Fulkerson 最大流（有向图）"""
    source = st.session_state.get("net_mf_s", "A")
    sink = st.session_state.get("net_mf_t", "B")

    # 构建有向图
    G = nx.DiGraph()
    for u, v, w in edges:
        G.add_edge(u, v, capacity=w)

    if source not in G or sink not in G:
        alert("源点或汇点不在图中", "error")
        return

    if source == sink:
        alert("源点和汇点不能相同", "error")
        return

    try:
        flow_value, flow_dict = nx.maximum_flow(G, source, sink)
    except Exception as e:
        alert(f"计算失败：{e}", "error")
        return

    # 提取有流量的边
    flow_edges = []
    flow_data = []
    for u in flow_dict:
        for v, f in flow_dict[u].items():
            if f > 1e-10:
                flow_edges.append((u, v))
                cap = G[u][v]['capacity']
                flow_data.append({
                    "边": f"{u} → {v}",
                    "容量": fmt(cap, 0),
                    "流量": fmt(f, 1),
                    "利用率": fmt((f / cap) * 100, 0) + "%" if cap > 0 else "—",
                })

    node_colors = {source: '#10b981', sink: '#ef4444'}

    # 画图时用无向布局但保留有向边信息
    G_undirected = _build_graph(edges)
    fig = _draw_network(G_undirected, highlighted_edges=flow_edges, node_colors=node_colors,
                        title=f"Max Flow: {source} → {sink} = {fmt(flow_value, 0)}")
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 💧 最大流结果")
        st.metric("最大流量", fmt(flow_value, 0))

    with col2:
        if flow_data:
            st.dataframe(pd.DataFrame(flow_data), use_container_width=True, hide_index=True)
