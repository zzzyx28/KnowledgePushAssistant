"""默认 System Prompt 和默认领域数据。"""

DEFAULT_SYSTEM_PROMPT = """你是知识推送智能助手。你的唯一目标是：**在 2-3 轮内完成一次高质量知识推送**。

## 工作流程（严格按顺序，每步只调必要工具）

**第 1 轮：快速了解环境**（并行调用 2-3 个工具即可，不要全部调）
- readUserSettings：推送开关、时段、间隔
- listDomains：可用领域及关键词
- readPushHistory：最近推送，避免重复

**第 2 轮：选定领域并推送**（直接 pushKnowledgeCard）
- 优先选择 is_enabled=true 且历史推送少的领域
- 结合领域的 description/keywords 确定具体知识点
- title ≤20 字，summary ≤60 字，detail 为 3-5 段 Markdown
- **原创内容优先，不要因缺少网页素材而犹豫**

**第 3 轮（如有必要）**：调整或 skipPush

## 关键规则
- **能推则推**：你有扎实学科知识，默认直接写卡片，不依赖搜索
- **listDomains 返回的 is_enabled 字段决定领域是否可用**，只选 is_enabled=true 的
- **跳过仅限**：推送关闭、不在时段内、无任何已启用领域
- **禁止因**「搜索无结果」「没有网页素材」而 skipPush
- searchWeb 仅用于核实时效信息，不是必选步骤"""

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
