"""
运输问题求解模块
================
求解产销平衡运输问题：m个产地、n个销地，已知运价矩阵和供需量，
找出使总运费最小的调运方案。

算法流程（标准运筹学方法）：
1. 初始可行解 → 最小元素法（贪心）或 伏格尔法（Vogel，考虑机会成本，通常更优）
2. 最优性检验 → 位势法（MODI），计算非基变量的检验数
3. 如果不是最优 → 闭回路法调整，回到步骤2
4. 所有检验数 ≥ 0 → 得到最优解

自动处理供需不平衡（添加虚拟产地/销地，运价为0）。
"""
import streamlit as st
import pandas as pd
import math
import copy
from src.utils.stats import fmt, parse_num
from src.utils.ui import alert


def render_transportation():
    st.markdown("## 🚚 运输问题求解")
    st.caption("求解运输问题的初始可行方案，使用位势法判断最优性，闭回路法调整至最优解。")

    # 问题规模
    col1, col2, col3 = st.columns(3)
    with col1:
        m = st.number_input("产地数 m", value=3, min_value=1, max_value=10, step=1, key="tp_m")
    with col2:
        n = st.number_input("销地数 n", value=4, min_value=1, max_value=10, step=1, key="tp_n")

    st.markdown("#### 📋 运价矩阵 & 供需量")

    # 用 data_editor 输入矩阵
    costs = [[3, 11, 3, 10], [1, 9, 2, 8], [7, 4, 10, 5]]
    supply = [7.0, 4.0, 9.0]
    demand = [3.0, 6.0, 5.0, 6.0]

    # 构建 DataFrame
    matrix_data = {}
    for i in range(min(m, len(costs))):
        row_costs = costs[i] if i < len(costs) else [0] * n
        row_s = supply[i] if i < len(supply) else 0
        # pad or truncate
        while len(row_costs) < n:
            row_costs.append(0)
        matrix_data[f"产地 {chr(65+i)}"] = row_costs[:n] + [row_s]
    for i in range(len(costs), m):
        matrix_data[f"产地 {chr(65+i)}"] = [0] * n + [0]

    # 需求量行
    demand_row = demand[:n] + [None]
    while len(demand_row) < n + 1:
        demand_row.insert(-1, 0)
    matrix_data["需求量"] = demand_row[:n] + [None]

    col_labels = [f"销地 {chr(66+j)}" for j in range(n)] + ["供应量"]

    df = pd.DataFrame(matrix_data, index=col_labels).T

    edited_df = st.data_editor(df, use_container_width=True, key="tp_editor")

    # 按钮
    btn_cols = st.columns(3)
    with btn_cols[0]:
        solve_min = st.button("最小元素法求初始解", use_container_width=True)
    with btn_cols[1]:
        solve_vogel = st.button("伏格尔法求初始解", use_container_width=True)
    with btn_cols[2]:
        solve_opt = st.button("位势法检验 + 闭回路调整至最优", use_container_width=True)

    if solve_min or solve_vogel or solve_opt:
        # 读取矩阵
        costs_m, supply_v, demand_v = _read_tp_matrix(edited_df, m, n)
        if costs_m is None:
            return

        method = "min-cost" if solve_min else "vogel" if solve_vogel else "optimize"

        if method == "optimize":
            if "tp_solution" not in st.session_state:
                alert("请先使用最小元素法或伏格尔法求解初始方案", "error")
                return
            sol = copy.deepcopy(st.session_state.tp_solution)
            _optimize_tp(costs_m, supply_v, demand_v, sol)
        else:
            sol = _solve_initial(costs_m, supply_v, demand_v, method)
            st.session_state.tp_solution = copy.deepcopy(sol)
            st.session_state.tp_optimal = False
            total_cost = _tp_total_cost(costs_m, sol)
            title = "最小元素法" if method == "min-cost" else "伏格尔法 (Vogel)"
            _display_tp_solution(costs_m, supply_v, demand_v, sol, title, total_cost,
                                 optimal=False)


def _read_tp_matrix(df, m, n):
    """读取运输问题矩阵"""
    costs = []
    supply = []
    for i in range(m):
        row_name = f"产地 {chr(65+i)}"
        if row_name not in df.index:
            alert(f"找不到行：{row_name}", "error")
            return None, None, None
        row = df.loc[row_name]
        row_costs = []
        for j in range(n):
            col_name = f"销地 {chr(66+j)}"
            val = parse_num(str(row[col_name])) if col_name in df.columns else 0
            row_costs.append(val if not math.isnan(val) else 0)
        costs.append(row_costs)
        s_val = parse_num(str(row["供应量"])) if "供应量" in df.columns else 0
        supply.append(s_val if not math.isnan(s_val) else 0)

    demand = []
    demand_row = df.loc["需求量"] if "需求量" in df.index else None
    for j in range(n):
        col_name = f"销地 {chr(66+j)}"
        d_val = parse_num(str(demand_row[col_name])) if demand_row is not None and col_name in df.columns else 0
        demand.append(d_val if not math.isnan(d_val) else 0)

    return costs, supply, demand


def _solve_initial(costs, supply, demand, method):
    """求解初始可行解"""
    m, n = len(costs), len(costs[0])
    s = supply[:]
    d = demand[:]

    # 检查平衡
    sum_s, sum_d = sum(s), sum(d)
    if abs(sum_s - sum_d) > 1e-10:
        if sum_s < sum_d:
            costs = costs + [[0] * n]
            s = s + [sum_d - sum_s]
        else:
            costs = [row + [0] for row in costs]
            d = d + [sum_s - sum_d]

    if method == "min-cost":
        return _min_cost_method(costs, s, d)
    else:
        return _vogel_method(costs, s, d)


def _min_cost_method(costs, supply, demand):
    """最小元素法"""
    m, n = len(costs), len(costs[0])
    sol = [[None] * n for _ in range(m)]
    s = supply[:]
    d = demand[:]

    # 收集所有单元格，按成本排序
    cells = [(costs[i][j], i, j) for i in range(m) for j in range(n)]
    cells.sort()

    for _, i, j in cells:
        if s[i] <= 1e-10 or d[j] <= 1e-10:
            continue
        alloc = min(s[i], d[j])
        sol[i][j] = alloc
        s[i] -= alloc
        d[j] -= alloc

    return sol


def _vogel_method(costs, supply, demand):
    """伏格尔法"""
    m, n = len(costs), len(costs[0])
    sol = [[None] * n for _ in range(m)]
    s = supply[:]
    d = demand[:]
    active_rows = set(range(m))
    active_cols = set(range(n))

    while active_rows and active_cols:
        max_penalty = -1
        best_cell = None

        # 行罚数
        for i in list(active_rows):
            row_costs = [(costs[i][j], j) for j in active_cols]
            row_costs.sort()
            penalty = row_costs[1][0] - row_costs[0][0] if len(row_costs) > 1 else row_costs[0][0]
            if penalty > max_penalty:
                max_penalty = penalty
                best_cell = (i, row_costs[0][1])

        # 列罚数
        for j in list(active_cols):
            col_costs = [(costs[i][j], i) for i in active_rows]
            col_costs.sort()
            penalty = col_costs[1][0] - col_costs[0][0] if len(col_costs) > 1 else col_costs[0][0]
            if penalty > max_penalty:
                max_penalty = penalty
                best_cell = (col_costs[0][1], j)

        if not best_cell:
            break

        i, j = best_cell
        alloc = min(s[i], d[j])
        sol[i][j] = (sol[i][j] or 0) + alloc
        s[i] -= alloc
        d[j] -= alloc

        if s[i] <= 1e-10:
            active_rows.discard(i)
        if d[j] <= 1e-10:
            active_cols.discard(j)

    return sol


def _modi_method(costs, sol):
    """位势法 (MODI)"""
    m, n = len(costs), len(costs[0])
    u = [None] * m
    v = [None] * n
    u[0] = 0

    changed = True
    while changed:
        changed = False
        for i in range(m):
            for j in range(n):
                if sol[i][j] is not None:
                    if u[i] is not None and v[j] is None:
                        v[j] = costs[i][j] - u[i]
                        changed = True
                    elif v[j] is not None and u[i] is None:
                        u[i] = costs[i][j] - v[j]
                        changed = True

    # 计算检验数
    deltas = [[None] * n for _ in range(m)]
    all_non_neg = True
    min_delta = float('inf')
    enter_cell = None

    for i in range(m):
        for j in range(n):
            if sol[i][j] is None and u[i] is not None and v[j] is not None:
                delta = costs[i][j] - u[i] - v[j]
                deltas[i][j] = delta
                if delta < -1e-10:
                    all_non_neg = False
                    if delta < min_delta:
                        min_delta = delta
                        enter_cell = (i, j)

    return u, v, deltas, all_non_neg, enter_cell


def _find_closed_path(sol, start_i, start_j):
    """闭回路法找环"""
    m, n = len(sol), len(sol[0])
    occupied = set()
    for i in range(m):
        for j in range(n):
            if sol[i][j] is not None:
                occupied.add((i, j))
    occupied.add((start_i, start_j))

    path = [(start_i, start_j)]

    def dfs(i, j, direction):
        if len(path) > 1 and i == start_i and j == start_j:
            return True

        if direction == 'row':
            for jj in range(n):
                if jj == j:
                    continue
                if (i, jj) not in occupied:
                    continue
                if jj == start_j and i == start_i and len(path) > 2:
                    return True
                path.append((i, jj))
                if dfs(i, jj, 'col'):
                    return True
                path.pop()
        else:
            for ii in range(m):
                if ii == i:
                    continue
                if (ii, j) not in occupied:
                    continue
                if ii == start_i and j == start_j and len(path) > 2:
                    return True
                path.append((ii, j))
                if dfs(ii, j, 'row'):
                    return True
                path.pop()

        return False

    if dfs(start_i, start_j, 'row'):
        return path
    return None


def _adjust_by_closed_path(sol, path):
    """闭回路调整"""
    theta = float('inf')
    for k in range(1, len(path), 2):
        i, j = path[k]
        if sol[i][j] is not None and sol[i][j] < theta:
            theta = sol[i][j]

    if theta == float('inf'):
        return False

    for k, (i, j) in enumerate(path):
        if k % 2 == 0:
            sol[i][j] = (sol[i][j] or 0) + theta
        else:
            sol[i][j] -= theta
            if abs(sol[i][j]) < 1e-10:
                sol[i][j] = None

    return True


def _tp_total_cost(costs, sol):
    """计算总成本"""
    total = 0
    for i in range(len(costs)):
        for j in range(len(costs[0])):
            if sol[i][j] is not None:
                total += costs[i][j] * sol[i][j]
    return total


def _optimize_tp(costs, supply, demand, sol):
    """优化至最优解"""
    m, n = len(costs), len(costs[0])
    cur_sol = copy.deepcopy(sol)
    iterations = 0
    max_iter = 50
    history = []

    while iterations < max_iter:
        _, _, deltas, optimal, enter_cell = _modi_method(costs, cur_sol)
        if optimal:
            st.session_state.tp_optimal = True
            break

        if not enter_cell:
            break

        i, j = enter_cell
        path = _find_closed_path(cur_sol, i, j)
        if not path:
            break

        theta = min(cur_sol[p[0]][p[1]] for p in path[1::2] if cur_sol[p[0]][p[1]] is not None)
        history.append({
            "iter": iterations + 1,
            "enter_cell": enter_cell,
            "delta": deltas[i][j],
            "path": path,
            "theta": theta,
        })

        if not _adjust_by_closed_path(cur_sol, path):
            break

        iterations += 1

    total_cost = _tp_total_cost(costs, cur_sol)
    st.session_state.tp_solution = copy.deepcopy(cur_sol)

    _display_tp_solution(costs, supply, demand, cur_sol,
                         "最优解（位势法检验通过）" if st.session_state.tp_optimal else f"迭代{iterations}次后",
                         total_cost, optimal=st.session_state.tp_optimal, history=history)


def _display_tp_solution(costs, supply, demand, sol, title, total_cost, optimal=False, history=None):
    """展示运输问题解"""
    st.markdown(f"#### 🚚 {title}")
    st.metric("总运输成本", f"{fmt(total_cost)} 元")

    m, n = len(costs), len(costs[0])

    # 解矩阵
    sol_data = {}
    for i in range(m):
        row_vals = []
        for j in range(n):
            if sol[i][j] is not None:
                row_vals.append(f"{fmt(sol[i][j])} ({costs[i][j]})")
            else:
                row_vals.append(f"— ({costs[i][j]})")
        row_vals.append(fmt(supply[i]))
        sol_data[f"产地 {chr(65+i)}"] = row_vals

    demand_row = [fmt(d) for d in demand[:n]] + [""]
    sol_data["需求量"] = demand_row

    col_labels = [f"销地 {chr(66+j)}" for j in range(n)] + ["供应量"]
    sol_df = pd.DataFrame(sol_data, index=col_labels).T

    # 高亮非零单元格
    def highlight_nonzero(val):
        if val.startswith('—'):
            return 'color: #cbd5e1'
        elif '(' in val:
            return 'background-color: #dbeafe; font-weight: 600'
        return ''

    st.dataframe(sol_df.style.applymap(highlight_nonzero), use_container_width=True)

    if optimal and history is not None and len(history) > 0:
        with st.expander(f"🔄 优化过程 (共 {len(history)} 次迭代)", expanded=False):
            for h in history:
                i, j = h["enter_cell"]
                st.markdown(f"""
                **第 {h['iter']} 次调整**：入基格 ({i+1},{j+1})，检验数 = {fmt(h['delta'])}
                闭回路：{' → '.join(f'({p[0]+1},{p[1]+1})' for p in h['path'])}
                调整量 θ = {fmt(h['theta'])}
                """)

    if optimal:
        alert("当前解已是最优解，所有非基变量的检验数 ≥ 0。", "success")
    elif history is None:
        alert("点击「位势法检验 + 闭回路调整至最优」可继续优化至最优解。", "info")
