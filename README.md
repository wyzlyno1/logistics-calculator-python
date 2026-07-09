# 📦 物流计算工具箱 — Logistics Calculator

[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.37-FF4B4B)](https://streamlit.io/)
[![Plotly](https://img.shields.io/badge/Plotly-5.22-3F4F75)](https://plotly.com/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

面向物流工程专业的综合性 Web 计算平台。覆盖**库存管理、物流规划、需求预测**三大领域共 10 个核心算法模块。纯 Python 实现，Streamlit + Plotly 构建交互式界面。

## 🚀 在线体验

> 🌐 **在线体验**：https://logistics-calculator-python-byqyyruw836newk7ah8ppy.streamlit.app

本地运行：
```bash
pip install -r requirements.txt
streamlit run app.py
```

浏览器打开 `http://localhost:8501`

## 🧩 功能模块

### 库存管理
| 模块 | 核心算法 | 说明 |
|------|----------|------|
| 📦 经济订货批量 (EOQ) | √(2DS/H) | 基本EOQ、数量折扣分析、允许缺货模型 |
| 🏭 经济生产批量 (EPQ) | √(2DS/[H(1-d/p)]) | 边生产边消耗场景，含EOQ对比 |
| 🛡️ 安全库存计算 | SS = Z·σ·√L | 需求不确定/提前期不确定/综合模型 |
| 📊 ABC 分类分析 | 帕累托法则 | 按年消耗金额自动分类 + 双轴帕累托图 |

### 物流规划
| 模块 | 核心算法 | 说明 |
|------|----------|------|
| 📍 重心法选址 | 迭代重心法 | 多需求点最优选址 + 收敛可视化 |
| 🏢 选址案例分析 | 因素评分法 + 盈亏平衡法 | 多方法对比决策 |
| 🚚 运输问题求解 | 伏格尔法 + MODI位势法 + 闭回路法 | 产销平衡运输问题最优解 |
| 🕸️ 物流网络优化 | Dijkstra / Prim / Ford-Fulkerson | 图论算法 + NetworkX可视化 |

### 需求管理
| 模块 | 核心方法 | 说明 |
|------|----------|------|
| 📈 需求预测 | 移动平均/加权移动平均/指数平滑 | 含MAD/MSE/MAPE误差评估 |
| 🐂 牛鞭效应演示 | Order-up-to策略 | 四级供应链动态仿真 |

## 🛠 技术栈

| 层 | 技术 | 用途 |
|----|------|------|
| Web框架 | **Streamlit** | 零前端代码构建Web界面 |
| 可视化 | **Plotly** | 交互式图表（支持缩放/悬停/导出） |
| 图算法 | **NetworkX** | 网络优化模块的图构建与算法验证 |
| 数据处理 | **Pandas + NumPy** | 矩阵运算、时间序列分析 |

## 📁 项目结构

```
logistics-calculator-python/
├── app.py                    # 主入口：侧边栏导航 + 模块路由
├── requirements.txt          # 依赖清单
└── src/
    ├── inventory/            # 库存管理（4个模块）
    │   ├── eoq.py            #   经济订货批量
    │   ├── epq.py            #   经济生产批量
    │   ├── safety_stock.py   #   安全库存
    │   └── abc.py            #   ABC分类
    ├── planning/             # 物流规划（4个模块）
    │   ├── gravity.py        #   重心法选址
    │   ├── location.py       #   选址案例分析
    │   ├── transportation.py #   运输问题求解
    │   └── network.py        #   物流网络优化
    ├── demand/               # 需求管理（2个模块）
    │   ├── forecasting.py    #   需求预测
    │   └── bullwhip.py       #   牛鞭效应演示
    └── utils/                # 工具模块
        ├── stats.py          #   Z值表、正态分布、格式化
        └── ui.py             #   Streamlit通用UI组件
```

## 📸 预览

<!-- 运行后截图替换此处的占位文字 -->
启动后界面包含：
- 左侧边栏：分类导航（首页/库存管理/物流规划/需求管理）
- 主区域：参数输入表单 + 计算结果指标卡片 + Plotly交互图表 + 逐步求解过程

## 🎯 适用场景

- **课程学习**：物流工程、供应链管理课程的算法验证
- **作业辅助**：输入题目参数，输出完整解题步骤
- **项目展示**：Python全栈开发能力的证明

## 👤 作者

**湫** · 营口理工学院 · 物流工程专业

---

*所有计算基于物流工程教材标准公式。代码自主编写，MIT协议开源。*
