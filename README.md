# Knowledge Push Assistant

以 AI Agent 为核心的桌面端知识推送应用。定时推送个性化的知识卡片，支持用户自定义知识领域，结合网络搜索与大模型智能体自主决策生成内容。

## 快速启动

```bash
pip install -r requirements.txt
python run.py
```

## 项目结构

```
├── run.py                  # 启动入口
├── requirements.txt
├── src/
│   ├── main.py             # 应用入口：初始化、系统托盘、调度器
│   ├── config.py           # 配置管理
│   ├── agent/
│   │   ├── react_loop.py   # ReAct 循环生成器
│   │   ├── tools.py        # Agent 工具（JSON Schema + 实现）
│   │   └── defaults.py     # 默认 System Prompt 和领域数据
│   ├── llm/
│   │   └── client.py       # OpenAI 兼容客户端
│   ├── search/
│   │   └── web_search.py   # DuckDuckGo 搜索 + 网页抓取
│   ├── storage/
│   │   ├── models.py       # SQLAlchemy 模型
│   │   ├── repository.py   # 数据访问层
│   │   └── migrations.py   # 自动建表 + 默认数据
│   ├── scheduler/
│   │   └── push_scheduler.py  # 定时推送调度器
│   └── ui/
│       ├── main_window.py  # 主窗口
│       ├── title_bar.py    # 自定义标题栏
│       ├── sidebar.py      # 侧边栏导航
│       ├── popup.py        # 知识卡片弹出窗口
│       ├── detail_window.py # 学习详情窗口
│       ├── styles.py       # 全局样式常量
│       └── pages/
│           ├── dashboard.py     # 仪表盘
│           ├── agent_panel.py   # Agent 执行面板
│           ├── knowledge.py     # 知识管理
│           ├── domain_manager.py # 领域管理
│           ├── settings.py      # 推送设置
│           └── chat.py          # 教学对话
```

## 核心特性

- **Agent 优先**：ReAct Agent 自主决策推不推、推什么、怎么推
- **零硬编码**：领域、System Prompt、文案均可通过 UI 配置
- **流式可见**：Agent 每一步思考/工具调用/结果在 UI 中实时展示
- **模型无关**：支持任意 OpenAI 兼容 API（DeepSeek、OpenAI、Ollama 等）

## 配置

- 首次启动自动创建默认领域和 System Prompt
- 在「推送设置」页面配置 API Key、Base URL 和模型名称
- 在「领域管理」页面自定义知识领域
