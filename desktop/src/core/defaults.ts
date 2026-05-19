import type { AppSettings } from "./types";

export const DEFAULT_SETTINGS: AppSettings = {
  push_enabled: true,
  push_interval_minutes: 60,
  push_start_hour: 8,
  push_end_hour: 22,
  model_name: "deepseek-chat",
  model_base_url: "https://api.deepseek.com",
  model_api_key: "",
  user_preference_prompt: ""
};

export const DEFAULT_DOMAINS = [
  {
    name: "计算机基础",
    description: "编程、数据结构、算法、网络与操作系统核心知识",
    keywords: "编程 数据结构 算法 网络 操作系统 Linux 数据库"
  },
  {
    name: "人工智能",
    description: "机器学习、深度学习、NLP、Agent、RAG 与工程实践",
    keywords: "机器学习 深度学习 NLP 大模型 Agent RAG"
  }
];
