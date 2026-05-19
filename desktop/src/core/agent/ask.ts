import type { AppSettings, KnowledgeItem } from "../types";

const ASK_SYSTEM_TEMPLATE = `你是教学助手。用户正在阅读一条已推送的知识卡片，请**仅根据**下方卡片内容回答追问。

要求：
- 可延展讲解、举例、类比，但不得编造卡片中未出现的事实并声称为卡片内容。
- 若问题超出卡片范围，说明边界并基于卡片相关内容尽可能回答。
- 使用中文，结构清晰，适当分点。

--- 知识卡片 ---
【领域】{domain_name}
【标题】{title}
【摘要】{summary}
【详情】
{detail}
--- 卡片结束 ---`;

export type AskMessage = { role: "user" | "assistant"; content: string };

export function buildAskSystemPrompt(item: KnowledgeItem): string {
  return ASK_SYSTEM_TEMPLATE.replace("{domain_name}", item.domain_name || "未分类")
    .replace("{title}", item.title || "无标题")
    .replace("{summary}", item.summary || "（无摘要）")
    .replace("{detail}", item.detail || "（无详情）");
}

export async function askKnowledgeQuestion(input: {
  settings: AppSettings;
  item: KnowledgeItem;
  messages: AskMessage[];
}): Promise<string> {
  const { settings, item, messages } = input;
  if (!settings.model_api_key.trim()) {
    throw new Error("请先在「设置」中配置 API Key。");
  }

  const res = await fetch(`${settings.model_base_url}/chat/completions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${settings.model_api_key}`
    },
    body: JSON.stringify({
      model: settings.model_name,
      messages: [
        { role: "system", content: buildAskSystemPrompt(item) },
        ...messages.map((m) => ({ role: m.role, content: m.content }))
      ],
      temperature: 0.5,
      max_tokens: 1200
    })
  });

  if (!res.ok) {
    throw new Error(`模型请求失败: ${res.status}`);
  }

  const json = (await res.json()) as {
    choices?: Array<{ message?: { content?: string } }>;
  };
  const content = json.choices?.[0]?.message?.content?.trim();
  if (!content) {
    throw new Error("模型未返回有效回答。");
  }
  return content;
}
