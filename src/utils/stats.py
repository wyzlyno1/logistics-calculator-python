"""统计工具：Z 值表、格式化函数"""

# 标准正态分布 Z 值表（服务水平% -> Z值）
Z_TABLE: dict[float, float] = {
    50.00: 0.000,
    60.00: 0.253,
    70.00: 0.524,
    75.00: 0.674,
    80.00: 0.842,
    84.13: 1.000,
    85.00: 1.036,
    90.00: 1.282,
    91.00: 1.341,
    92.00: 1.405,
    93.00: 1.476,
    94.00: 1.555,
    95.00: 1.645,
    96.00: 1.751,
    97.00: 1.881,
    97.50: 1.960,
    98.00: 2.054,
    99.00: 2.326,
    99.50: 2.576,
    99.87: 3.000,
    99.90: 3.090,
    99.99: 3.719,
}

# 常用服务水平列表
COMMON_SERVICE_LEVELS = [90, 95, 97, 98, 99, 99.5]


def get_z_value(service_level: float) -> float | None:
    """根据服务水平获取 Z 值，使用线性插值"""
    sl = service_level  # 已经是百分比值，如 95 表示 95%
    keys = sorted(Z_TABLE.keys())

    # 精确匹配
    if sl in Z_TABLE:
        return Z_TABLE[sl]

    # 线性插值
    for i in range(len(keys) - 1):
        if keys[i] < sl < keys[i + 1]:
            t = (sl - keys[i]) / (keys[i + 1] - keys[i])
            return Z_TABLE[keys[i]] + t * (Z_TABLE[keys[i + 1]] - Z_TABLE[keys[i]])

    return None


def fmt(num: float, decimals: int = 2) -> str:
    """数值格式化"""
    if num == float('inf') or num == float('-inf') or (isinstance(num, float) and num != num):
        return '—'
    return f"{num:,.{decimals}f}"


def parse_num(s: str) -> float:
    """解析数字字符串，支持中文逗号"""
    if isinstance(s, (int, float)):
        return float(s)
    if not s:
        return float('nan')
    return float(s.replace(',', '').replace('，', '').strip())
