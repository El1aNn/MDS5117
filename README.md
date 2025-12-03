# 全球大豆贸易可视化看板 (Global Soybean Trade Dashboard)

这是一个基于 Python Streamlit 的交互式数据可视化项目，旨在分析全球大豆贸易的流动、竞争格局以及地缘政治事件（如中美贸易战）对市场的冲击。

## 📋 项目简介

本项目使用 BACI 国际贸易数据库，对 2012 年至 2023 年的大豆贸易数据（HS Code: 120110, 120190）进行清洗和可视化。

主要功能包括：

- **🌏 贸易流向与网络**：通过地理流向图和桑基图展示全球贸易概览。
- **🏆 竞争与排名**：展示主要出口国的市场地位演变。
- **🔍 国家概况**：深入分析特定国家的进出口平衡与贸易伙伴。
- **🕸️ 多路线分析**：对比不同贸易路线（如美国->中国 vs 巴西->中国）的流量与价格变化，直观呈现贸易战影响。

## 🛠️ 环境安装

本项目依赖 Python 3.x 及以下第三方库。建议创建一个虚拟环境进行管理。

### 1. 安装依赖

请确保已安装 `pip`，然后在终端运行以下命令安装所需库：

```bash
pip install pandas numpy streamlit plotly
```

主要依赖库说明：

- `streamlit`: 用于构建交互式 Web 应用
- `pandas`: 用于数据处理与分析
- `plotly`: 用于绘制交互式图表
- `numpy`: 用于数值计算

## 🚀 使用指南

### 第一步：数据准备

在启动看板之前，需要先运行数据处理脚本，从原始 BACI 数据集中提取大豆贸易数据并生成中间文件。

在项目根目录下运行：

```bash
python prepare_dashboard_data.py
```

> **注意**：该脚本会读取 `data/` 目录下的 CSV 文件，处理完成后会在 `data/` 目录下生成 `dashboard_data.csv` 文件。如果该文件已存在且无需更新，可跳过此步。

### 第二步：启动看板

数据准备就绪后，使用 Streamlit 启动可视化应用：

```bash
streamlit run dashboard_app.py
```

运行成功后，终端会显示访问地址（通常为 `http://localhost:8501`），浏览器会自动打开该页面。

## 📂 项目结构

```
.
├── dashboard_app.py          # Streamlit 可视化主程序
├── prepare_dashboard_data.py # 数据预处理脚本
├── data/                     # 数据文件夹
│   ├── BACI_HS12_Y*.csv      # 原始贸易数据 (需自行下载或提供)
│   ├── country_codes_*.csv   # 国家代码对照表
│   ├── product_codes_*.csv   # 产品代码对照表
│   └── dashboard_data.csv    # [生成文件] 预处理后的看板数据
└── README.md                 # 项目说明文档
```

## 📝 演示流程建议

如果您需要使用此看板进行演示（例如展示中美贸易战的影响），建议按照以下顺序操作：

1. **Trade Flows**: 展示 2012-2017 年的全球贸易概览。
2. **Competition**: 展示 2018 年前后出口国排名的变化。
3. **Multi-Route Analysis**: 重点对比 "USA -> China" 与 "Brazil -> China" 的贸易量与价格趋势。
