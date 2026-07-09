# CLAUDE.md — 物流计算工具箱 Python 版

## 项目概述

用 Python + Streamlit + Plotly 重建的物流工程计算工具箱。覆盖库存管理、物流规划、需求预测共 10 个模块。

原 HTML/JS 版位于 `D:/物流计算工具箱/`，算法逻辑照搬，只改语言。

## 环境

- **Python**: D:/anconda/python.exe
- **包管理**: pip（不用 conda env）
- **运行**: `streamlit run app.py`

## 项目结构

```
D:/物流计算工具箱-python/
├── app.py                    # 主入口：侧边栏导航 + 路由
├── requirements.txt
├── CLAUDE.md
├── README.md
├── src/
│   ├── inventory/            # 库存管理（EOQ/EPQ/安全库存/ABC分类）
│   ├── planning/             # 物流规划（重心法/选址分析/运输问题/网络优化）
│   ├── demand/               # 需求管理（需求预测/牛鞭效应）
│   └── utils/                # 工具（Z表/格式化/通用UI）
```

## 架构约定

1. **计算与 UI 分离**：各模块文件暴露纯计算函数 + 一个 `render_xxx()` Streamlit 渲染函数
2. **app.py 只做路由**：侧边栏选模块 → lazy import → 调用 `render_xxx()`
3. **公式照搬原 JS 版**：`D:/物流计算工具箱/js/modules/*.js`
4. **图表用 Plotly**：替代原 Canvas 手绘，`st.plotly_chart()` 渲染

## 验证方式

- 运行 `streamlit run app.py`
- 用原 JS 版的示例数据输入，比对输出结果
- 检查图表正常渲染、无报错

## 冲突说明

- ortools（已装）和 streamlit 的 protobuf 版本冲突，本期项目不用 ortools，不受影响
