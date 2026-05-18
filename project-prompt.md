# 知识推送助手 · 项目构建 Prompt

将此 Prompt 交给 Claude Code 或其它编程 Agent，从头构建整个项目。

---

## 一、项目愿景

构建一个**以 AI Agent 为核心**的桌面端知识推送应用。面向学生用户，定时推送个性化的知识卡片，支持**用户自定义知识领域**，结合网络搜索与大模型智能体自主决策生成内容。

**核心差异**：不是"定时器触发 → 硬编码管道 → 生成内容"的传统推送系统。而是 **Agent 拥有所有工具，自主决定：推不推、推什么、怎么推**。

**核心原则**：项目中不得硬编码任何业务规则、领域列表、文案模板。一切均可由用户通过 UI 配置和自定义。

---

## 二、Agent 优先架构

### 2.1 核心理念

应用的心脏是一个 **ReAct Agent**。它不是一个被调用的 API，而是拥有工具、能做决策的智能体。使用最简单的实现方式：**while 循环 + OpenAI 兼容 SDK 的 tool calling**，不引入 LangChain 等重型框架。

```
定时器/用户触发 → Agent 启动 ReAct 循环：
  Thought → Action（调用工具）→ Observation → Thought → ...
  最终决策：pushKnowledgeCard() 或 skipPush()
```

### 2.2 实现方式

```python
# 核心骨架（不引入任何 Agent 框架）
def react_loop(messages, tools, max_turns=10):
    for step in range(max_turns):
        response = client.chat.completions.create(
            model=current_model,  # 用户配置
            messages=messages,
            tools=tools
        )
        msg = response.choices[0].message
        if msg.tool_calls:
            for tc in msg.tool_calls:
                yield {"type": "action", "tool": tc.function.name, "args": tc.function.arguments}
                result = execute_tool(tc.function.name, json.loads(tc.function.arguments))
                yield {"type": "observation", "tool": tc.function.name, "result": result}
                messages.append(msg)
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(result, ensure_ascii=False)})
        else:
            yield {"type": "final", "content": msg.content}
            return
```

> 用生成器 `yield` 将每一步推送给 UI，实现 Agent 执行过程全透明。

### 2.3 Agent 拥有的工具

Agent 通过 Function Calling 机制调用以下工具。工具定义需同时提供 JSON Schema（给 LLM）和 Python 函数实现。


| 工具名                 | 用途               | 输入                                                       | 输出                   |
| ------------------- | ---------------- | -------------------------------------------------------- | -------------------- |
| `searchWeb`         | 搜索互联网获取知识素材      | query, topK                                              | 搜索结果列表               |
| `fetchWebContent`   | 抓取指定URL的网页正文     | url                                                      | 网页文本内容               |
| `readUserSettings`  | 读取用户推送设置         | 无                                                        | 完整设置对象               |
| `readPushHistory`   | 读取最近的推送记录        | limit                                                    | 推送历史列表               |
| `readUserFeedback`  | 读取用户反馈记录         | limit                                                    | 反馈列表                 |
| `getDomainStats`    | 获取各领域统计信息        | 无                                                        | 每个领域的知识条数、平均评分       |
| `getCurrentTime`    | 获取当前时间           | 无                                                        | 当前时间、星期几             |
| `listDomains`       | 获取用户自定义的所有知识领域   | 无                                                        | 领域列表（名称、描述、关键词、是否启用） |
| `pushKnowledgeCard` | 生成并保存知识卡片，触发推送通知 | domainId, title, summary, detail, sourceUrl, sourceTitle | 推送结果                 |
| `skipPush`          | 跳过本次推送           | reason                                                   | 跳过确认                 |


### 2.4 Agent System Prompt（核心）

System Prompt 本身也需可通过 UI 编辑。以下为默认值：

```
你是知识推送智能助手。你的任务是：

1. **了解用户**：
   - 通过 readUserSettings 了解推送偏好（频率、时间窗口、选中的领域）
   - 通过 readPushHistory 了解最近推送了什么，避免重复
   - 通过 readUserFeedback 了解用户的内容偏好（喜欢什么领域、什么风格）
   - 通过 getDomainStats 了解各领域的知识覆盖情况
   - 通过 listDomains 获取用户自定义的所有领域及其描述和关键词

2. **选择领域和角度**：
   - 用户反馈好的领域优先
   - 覆盖不足的领域适当补充
   - 避免连续推送同一领域
   - 参考领域配置中的"关键词"字段来构思搜索方向
   - 早上适合基础概念，晚上适合深度内容

3. **搜索素材**：
   - 用具体、有针对性的关键词搜索（结合领域关键词 + 角度词）
   - 如果搜索结果不理想，调整关键词重试（最多2次）
   - 对于有价值的链接，用 fetchWebContent 获取更多内容

4. **生成推送或跳过**：
   - 素材充足 → 生成知识卡片，调用 pushKnowledgeCard
   - 素材不足或时机不对 → 调用 skipPush 并说明原因
   - title 控制在20字以内，summary 控制在60字以内，detail 为3-5段Markdown

**重要原则**：
- 宁缺毋滥：没有好内容就跳过，不使用模板化凑数卡片
- 个性化：参考用户反馈历史，推送用户可能感兴趣的内容
- 多样性：避免连续推送同一领域
- 好奇驱动：每张卡片都应引发进一步学习的兴趣
- 尊重用户配置：用户自定义的领域描述和关键词是对推送方向的指引
```

> **该 System Prompt 必须在设置页面中可编辑**，让高级用户可以调整 Agent 的行为策略。

---

## 三、技术栈


| 层        | 技术                                | 理由                                               |
| -------- | --------------------------------- | ------------------------------------------------ |
| 桌面框架     | **PySide6** (Qt for Python)       | 轻量、启动快、内存低，适合常驻后台                                |
| 语言       | **Python 3.11+**                  | 与 PySide6 原生集成，LLM 生态成熟                          |
| LLM 调用   | **openai Python SDK**             | OpenAI 兼容协议的事实标准，DeepSeek / OpenAI / Ollama 全线兼容 |
| Agent 框架 | **无框架，自实现 ReAct 循环**              | 你的场景不需要图拓扑和持久化，200 行 while 循环完全可控                |
| 搜索       | **duckduckgo_search** 库           | 免费、无需 API Key                                    |
| 数据存储     | **SQLite** + **SQLAlchemy ORM**   | 单文件、零配置、适合本地桌面应用                                 |
| 通知       | 自定义 **Popup 窗口**（PySide6 QWidget） | 系统通知无法承载"知识卡片"的交互                                |
| 打包       | **PyInstaller**                   | Windows / macOS 各一条命令，CI 友好                      |


---

## 四、数据模型

### 4.1 核心原则

- **领域是用户数据，不是枚举**——用户可随时增删改
- **所有配置项持久化到 DB**，UI 提供编辑入口
- **推送历史是 Agent 的"记忆"**，Agent 每次决策前必须读取

### 4.2 模型定义

```python
# ── 知识领域（用户自定义，非硬编码） ──
class KnowledgeDomain:
    id: int (PK, 自增)
    name: str              # 领域名称，如 "计算机科学"（用户自定义）
    description: str       # 领域描述，如 "包括编程、算法、计算机网络、操作系统等"
    keywords: str          # 搜索关键词提示，如 "编程入门 数据结构 网络协议 Linux"
    icon: str              # 图标（emoji 或字符），如 "💻"
    sort_order: int        # 排序权重，越小越靠前
    is_enabled: bool       # 是否启用
    created_at: datetime
    updated_at: datetime

# ── 知识条目 ──
class KnowledgeItem:
    id: int (PK)
    domain_id: int (FK → KnowledgeDomain)
    domain_name: str       # 冗余字段，避免 JOIN
    title: str             # 卡片标题（≤20字）
    summary: str           # 卡片摘要（≤60字）
    detail: str            # 学习详情（Markdown 格式）
    source_url: str?       # 来源 URL
    source_title: str?     # 来源标题
    trust_score: float     # 0.0-1.0
    content_hash: str (UNIQUE)  # SHA-256 去重
    is_read: bool
    is_favorited: bool
    rating: int?           # 1=有用, -1=不感兴趣
    created_at: datetime

# ── 推送历史 ──
class PushHistory:
    id: int (PK)
    knowledge_item_id: int (FK → KnowledgeItem)
    pushed_at: datetime
    is_clicked: bool

# ── 用户设置（键值对） ──
class UserSettings:
    id: int (PK)
    key: str (UNIQUE)
    value: str             # JSON 序列化的值

# ── 对话消息 ──
class ChatMessage:
    id: int (PK)
    session_id: str
    role: str              # "user" | "assistant"
    content: str
    created_at: datetime

# ── Agent 执行日志（可观测性） ──
class AgentExecutionLog:
    id: int (PK)
    session_id: str
    step_type: str         # "thought" | "action" | "observation" | "final" | "error"
    tool_name: str?        # 调用的工具名
    tool_input: str?       # 工具入参 JSON
    tool_output: str?      # 工具出参 JSON
    content: str?          # 思考或最终输出文本
    created_at: datetime
```

### 4.3 默认数据

应用首次启动时自动创建以下默认数据，**用户可随时修改或删除**：

```python
DEFAULT_DOMAINS = [
    {
        "name": "计算机基础",
        "description": "编程入门、数据结构与算法、计算机网络、操作系统等计算机科学核心知识",
        "keywords": "编程入门 数据结构 算法 网络协议 操作系统 Linux 数据库",
        "icon": "💻"
    },
    {
        "name": "人工智能",
        "description": "机器学习、深度学习、自然语言处理、计算机视觉等AI领域知识",
        "keywords": "机器学习 深度学习 神经网络 NLP 大模型 RAG Agent",
        "icon": "🤖"
    },
    {
        "name": "机械工程",
        "description": "机械设计、材料力学、热力学、流体力学、制造工艺等工程知识",
        "keywords": "机械设计 材料科学 热力学 流体力学 CAD 制造工艺",
        "icon": "⚙️"
    }
]

DEFAULT_SYSTEM_PROMPT = """
你是知识推送智能助手。你的任务是：
... （见 2.4 节）
"""
```

> **关键**：默认数据仅用于首次启动引导。用户可在"领域管理"页面中增删改领域，在"设置"页面中编辑 System Prompt。

---

## 五、UI 设计

### 5.1 整体风格

- **浅色主题**：背景 `#f5f6fa`，卡片 `#ffffff`，文字 `#1a1d2e`
- **强调色**：靛蓝 `#6366f1`
- **字体**：Inter（正文）+ JetBrains Mono（代码/标签）
- **圆角**：12-16px
- **阴影**：轻量多层
- **frameless 窗口**：自定义标题栏（左侧品牌名+状态点，右侧窗口控制按钮）
- **标题栏可拖拽**、可最小化/最大化/关闭

### 5.2 窗口结构

```
┌──────────────────────────────────────────────────┐
│ ● Knowledge Push                   ─  □  ✕       │ ← 自定义标题栏
├──────────┬───────────────────────────────────────┤
│  侧边栏   │  内容区                                │
│          │                                       │
│  仪表盘   │  [页面标题 + 描述]                      │
│  知识管理 │                                       │
│  领域管理 │  [各页面的主体内容]                      │
│  推送设置 │                                       │
│  教学对话 │                                       │
│  Agent   │                                       │
│          │                                       │
│  🟢 在线  │                                       │
└──────────┴───────────────────────────────────────┘
```

### 5.3 页面清单（6 个页面）

**① 仪表盘**

- 三张指标卡：知识总量、最近条目（7天内）、推送状态
- "智能推送"按钮 → 触发 Agent，切换到 Agent 面板
- 最近 3 条知识卡片预览
- 各领域知识分布简图

**② Agent 执行面板（核心页面）**

- 点击"智能推送"后进入
- **时间线组件**，实时展示 Agent 每一步：
  - 💭 思考（文字气泡）
  - 🔧 工具调用（卡片：工具名 + 入参）
  - 👁 结果（摘要）
  - ✅ 最终决策
- 流式更新——用户看到 Agent "正在思考"和"正在行动"

**③ 知识管理**

- 知识卡片列表，按时间倒序
- 按领域筛选（下拉选择，领域列表从 DB 动态读取）
- 每条可：收藏、有用、不感兴趣、查看来源
- 搜索（标题/摘要模糊匹配）

**④ 领域管理（新增，体现可定制化）**

- 领域列表（表格），显示：图标、名称、描述摘要、关键词、状态、操作
- **新增领域**：弹窗表单——名称、描述、关键词、图标
- **编辑领域**：弹窗表单，预填现有值
- **删除领域**：确认对话框，提示已有 N 条知识会保留但失去领域关联
- **启用/禁用**：Toggle 开关
- **拖拽排序**：调整领域在列表中的显示顺序

**⑤ 推送设置**

- **推送配置**：
  - 推送开关（Toggle）
  - 间隔（分钟）、开始时间、结束时间
- **模型配置**：
  - 模型名称、Base URL、API Key（密码输入框）
  - "测试连接"按钮
- **Agent System Prompt 编辑器**（多行文本框，等宽字体）
  - 默认值预填，用户可自由编辑
  - "恢复默认"按钮
- **领域启用选择**：勾选哪些领域参与推送（列表从 DB 动态读取）

**⑥ 教学对话**

- Agent 驱动的对话（Agent 可查知识库 + 联网搜索来回答）
- 对话气泡（用户蓝底靠右，AI 白底靠左）
- 输入框 + 发送按钮
- 对话历史持久化

### 5.4 系统托盘

- 托盘图标 + Tooltip
- 右键菜单：打开主面板、立即推送一条、退出
- 双击托盘 → 打开主面板

### 5.5 知识卡片弹出窗口（Popup）

- 定时推送时弹出
- 显示：领域标签 + 图标、标题、摘要
- 点击 → 展开详细窗口（Markdown 渲染 + 来源链接 + 收藏/评价按钮）
- 5 秒自动消失或用户手动关闭

---

## 六、项目结构

```
knowledge-push/
├── src/
│   ├── __init__.py
│   ├── main.py                     # 入口：初始化应用、系统托盘、调度器
│   ├── config.py                   # 配置管理：首次启动创建默认数据
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── react_loop.py           # ReAct 循环生成器
│   │   ├── tools.py                # 所有工具函数的 JSON Schema + 实现
│   │   └── defaults.py             # 默认 System Prompt 和默认领域数据
│   ├── llm/
│   │   ├── __init__.py
│   │   └── client.py               # OpenAI 兼容客户端 + Tool Calling
│   ├── search/
│   │   ├── __init__.py
│   │   └── web_search.py           # DuckDuckGo 搜索 + 网页内容抓取
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── models.py               # SQLAlchemy 模型
│   │   ├── repository.py           # 数据访问层（CRUD 封装）
│   │   └── migrations.py           # 首次运行自动建表 + 插入默认数据
│   ├── scheduler/
│   │   ├── __init__.py
│   │   └── push_scheduler.py       # 定时触发 Agent
│   └── ui/
│       ├── __init__.py
│       ├── main_window.py          # 主窗口（frameless + 自定义标题栏）
│       ├── title_bar.py            # 自定义标题栏
│       ├── sidebar.py              # 侧边栏导航（菜单项含路由 + 图标）
│       ├── pages/
│       │   ├── __init__.py
│       │   ├── dashboard.py        # 仪表盘
│       │   ├── agent_panel.py      # Agent 执行面板（时间线）
│       │   ├── knowledge.py        # 知识管理
│       │   ├── domain_manager.py   # 领域管理（增删改查）
│       │   ├── settings.py         # 推送设置 + System Prompt 编辑
│       │   └── chat.py             # 教学对话
│       ├── popup.py                # 知识卡片弹出窗口
│       ├── detail_window.py        # 学习详情窗口
│       └── styles.py               # 全局样式常量（颜色、字体、圆角等）
├── resources/
│   └── icon.png                    # 应用图标
├── requirements.txt
└── README.md
```

---

## 七、实现顺序

### 第一阶段：基础设施（数据库 + LLM + 搜索）

1. 项目骨架：`requirements.txt`、`src/main.py`、`src/config.py`
2. 数据模型 + 自动建表 + 默认数据插入：`storage/models.py`、`storage/repository.py`、`storage/migrations.py`
3. LLM 客户端封装（Tool Calling）：`llm/client.py`
4. 搜索模块：`search/web_search.py`
5. 命令行集成测试：写脚本验证 "LLM 能调用搜索 Tool 并返回结果"

### 第二阶段：Agent 核心

1. Tool 定义（JSON Schema + 实现）：`agent/tools.py`
2. ReAct 循环生成器：`agent/react_loop.py`
3. 调度器：`scheduler/push_scheduler.py`
4. 命令行验证：让 Agent 完整跑一次推送决策

### 第三阶段：UI

1. 样式常量 + 主窗口 + 标题栏 + 侧边栏。浅色
2. 仪表盘页面
3. Agent 执行面板（重点——流式展示 + 时间线组件）
4. 知识管理页面
5. **领域管理页面**（新增/编辑/删除/排序/启禁用）
6. 推送设置页面（含 System Prompt 编辑器 + 测试连接）
7. 教学对话页面
8. Popup 弹出窗口 + 详情窗口

### 第四阶段：集成与发布

1. 系统托盘集成
2. 全链路联调：定时器 → Agent → 流式 UI → Popup
3. UI 打磨（动画、过渡、响应式）
4. PyInstaller 打包配置（Windows + macOS）
5. GitHub Actions CI（双平台自动构建）

---

## 八、关键约束

### 不可妥协

- **Agent 执行过程流式可见**：每一步 Thought / Action / Observation 必须在 UI 中实时展示
- **零硬编码**：领域、System Prompt、配色、所有文案均可由用户通过 UI 修改
- **中文优先**：UI 文案、代码注释、默认 System Prompt 均使用中文
- **模型无关**：支持任意 OpenAI 兼容 API（DeepSeek、OpenAI、Ollama 等），通过 Base URL + API Key 配置

### 设计原则

- **搜索失败时的行为**：Agent 应调用 `skipPush`，而非生成模板凑数卡片
- **去重机制**：SHA-256 对 (title + summary + detail) 做哈希，DB 唯一约束兜底
- **首次启动引导**：自动创建默认领域 + 默认 System Prompt，用户可立即使用
- **窗口**：frameless + 可拖拽 + 最小尺寸 900×600
- **配置持久化**：settings.json 存窗口位置/大小等静态配置，SQLite 存所有业务配置

---

## 九、依赖清单

```
# requirements.txt
PySide6>=6.5.0
openai>=1.0.0
duckduckgo_search>=5.0.0
SQLAlchemy>=2.0.0
APScheduler>=3.10.0
pyinstaller>=6.0.0
requests>=2.31.0
beautifulsoup4>=4.12.0
markdown>=3.5.0
```

**不引入**：langchain、langgraph、agno、crewai、autogen 等 Agent 框架。本项目用 openai SDK 的 tool calling + 自实现 while 循环完全足够。