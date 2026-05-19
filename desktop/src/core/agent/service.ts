import {
  createKnowledgeCard,
  getDomainStats,
  getRecentPushHistory,
  getSettings,
  getUserFeedback,
  listDomains,
  saveAgentLog
} from "../repository";
import type { Domain } from "../types";

export interface AgentResult {
  ok: boolean;
  message: string;
  sessionId: string;
  pushedItemId?: number;
  events: Array<{
    stepType: "thought" | "action" | "observation" | "final" | "error";
    content: string;
    toolName?: string;
    toolInput?: string;
    toolOutput?: string;
  }>;
}

export async function runAgentOnce(): Promise<AgentResult> {
  const sessionId = crypto.randomUUID();
  const events: AgentResult["events"] = [];
  const emit = async (event: AgentResult["events"][number]): Promise<void> => {
    events.push(event);
    await saveAgentLog({
      sessionId,
      stepType: event.stepType,
      content: event.content,
      toolName: event.toolName,
      toolInput: event.toolInput,
      toolOutput: event.toolOutput
    });
  };

  const settings = await getSettings();
  if (!settings.push_enabled) {
    await emit({ stepType: "final", content: "推送开关关闭，结束本轮。" });
    return { ok: false, message: "推送已关闭", sessionId, events };
  }
  const hour = new Date().getHours();
  if (!isWithinWindow(hour, settings.push_start_hour, settings.push_end_hour)) {
    await emit({ stepType: "final", content: `当前不在时段内（${hour}:00）。` });
    return { ok: false, message: "当前不在推送时段内", sessionId, events };
  }

  const tools = buildToolSchemas();
  const messages: ChatMessage[] = [
    { role: "system", content: buildSystemPrompt(settings.user_preference_prompt) },
    {
      role: "user",
      content:
        "请根据当前设置和历史，优先调用工具获取必要信息，然后做出最终决策：pushKnowledgeCard 或 skipPush。"
    }
  ];

  for (let turn = 0; turn < 6; turn += 1) {
    const assistant = await requestChat({
      baseUrl: settings.model_base_url,
      apiKey: settings.model_api_key,
      model: settings.model_name,
      messages,
      tools
    });

    if (assistant.content) {
      await emit({ stepType: "thought", content: assistant.content });
    }

    if (!assistant.tool_calls || assistant.tool_calls.length === 0) {
      await emit({
        stepType: "final",
        content: assistant.content || "模型未给出可执行工具调用，结束本轮。"
      });
      return { ok: false, message: "Agent 未调用工具完成决策", sessionId, events };
    }

    messages.push({
      role: "assistant",
      content: assistant.content || "",
      tool_calls: assistant.tool_calls
    });

    for (const toolCall of assistant.tool_calls) {
      const toolName = toolCall.function.name;
      const args = safeJsonParse<Record<string, unknown>>(toolCall.function.arguments, {});
      await emit({
        stepType: "action",
        content: `调用工具 ${toolName}`,
        toolName,
        toolInput: JSON.stringify(args, null, 2)
      });

      const output = await executeTool(toolName, args, settings);
      await emit({
        stepType: "observation",
        content: `${toolName} 返回`,
        toolName,
        toolOutput: output
      });
      messages.push({
        role: "tool",
        tool_call_id: toolCall.id,
        content: output
      });

      if (toolName === "pushKnowledgeCard") {
        const parsed = safeJsonParse<{ status?: string; title?: string; itemId?: number }>(output, {});
        const success = parsed.status === "success";
        await emit({
          stepType: "final",
          content: success ? `推送成功：${parsed.title || "知识卡片"}` : "推送未成功。"
        });
        return {
          ok: success,
          message: success ? `已推送：${parsed.title || "知识卡片"}` : "推送失败",
          sessionId,
          pushedItemId: parsed.itemId,
          events
        };
      }
      if (toolName === "skipPush") {
        const parsed = safeJsonParse<{ reason?: string }>(output, {});
        await emit({
          stepType: "final",
          content: `已跳过：${parsed.reason || "无原因"}`
        });
        return {
          ok: false,
          message: `本轮跳过：${parsed.reason || "无原因"}`,
          sessionId,
          events
        };
      }
    }
  }

  await emit({ stepType: "error", content: "达到最大轮次，仍未完成最终决策。" });
  return { ok: false, message: "达到最大执行轮次", sessionId, events };
}

function isWithinWindow(currentHour: number, start: number, end: number): boolean {
  if (start <= end) {
    return currentHour >= start && currentHour < end;
  }
  return currentHour >= start || currentHour < end;
}

async function generateCard(input: {
  baseUrl: string;
  apiKey: string;
  model: string;
  userPreference: string;
  domainName: string;
  domainKeywords: string;
}): Promise<{ title: string; summary: string; detail: string }> {
  const prompt = [
    "你是知识推送助手，请只输出 JSON，不要输出额外文本。",
    "字段必须为 title, summary, detail。",
    "title <= 20 字，summary <= 60 字，detail 为 3-5 段 Markdown。",
    `领域: ${input.domainName}`,
    `关键词: ${input.domainKeywords}`,
    input.userPreference ? `用户偏好: ${input.userPreference}` : ""
  ]
    .filter(Boolean)
    .join("\n");

  const payload = {
    model: input.model,
    messages: [{ role: "user", content: prompt }],
    temperature: 0.7,
    response_format: { type: "json_object" }
  };

  const res = await fetch(`${input.baseUrl}/chat/completions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${input.apiKey || "sk-placeholder"}`
    },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    throw new Error(`模型请求失败: ${res.status}`);
  }
  const data = (await res.json()) as {
    choices?: Array<{ message?: { content?: string } }>;
  };
  const content = data.choices?.[0]?.message?.content ?? "{}";
  let parsed: Partial<{ title: string; summary: string; detail: string }> = {};
  try {
    parsed = JSON.parse(content) as Partial<{ title: string; summary: string; detail: string }>;
  } catch {
    // model returned non-JSON; treat the raw content as the detail
    parsed = { detail: content };
  }
  return {
    title: (parsed.title ?? "今日知识推送").slice(0, 20),
    summary: (parsed.summary ?? "来自智能助手的知识摘要").slice(0, 60),
    detail: parsed.detail ?? "暂无详情"
  };
}

interface ChatMessage {
  role: "system" | "user" | "assistant" | "tool";
  content: string;
  tool_call_id?: string;
  tool_calls?: Array<{
    id: string;
    type?: string;
    function: { name: string; arguments: string };
  }>;
}

function buildSystemPrompt(userPreference: string): string {
  const preference = userPreference.trim();
  return [
    "你是知识推送智能助手。你要在 2-3 轮内完成高质量推送。",
    "优先读取设置、领域、历史、反馈，再决定具体领域。",
    "若适合推送，调用 pushKnowledgeCard；若不适合才调用 skipPush。",
    "title <= 20 字，summary <= 60 字，detail 为 3-5 段 Markdown。",
    preference ? `用户偏好: ${preference}` : ""
  ]
    .filter(Boolean)
    .join("\n");
}

function buildToolSchemas() {
  return [
    {
      type: "function",
      function: {
        name: "readUserSettings",
        description: "读取推送开关、间隔、时段和模型配置",
        parameters: { type: "object", properties: {}, required: [] }
      }
    },
    {
      type: "function",
      function: {
        name: "listDomains",
        description: "读取所有领域及启用状态",
        parameters: { type: "object", properties: {}, required: [] }
      }
    },
    {
      type: "function",
      function: {
        name: "readPushHistory",
        description: "读取最近推送历史",
        parameters: {
          type: "object",
          properties: { limit: { type: "integer", default: 10 } }
        }
      }
    },
    {
      type: "function",
      function: {
        name: "readUserFeedback",
        description: "读取用户评分和收藏反馈",
        parameters: {
          type: "object",
          properties: { limit: { type: "integer", default: 20 } }
        }
      }
    },
    {
      type: "function",
      function: {
        name: "getDomainStats",
        description: "获取领域维度统计和平均评分",
        parameters: { type: "object", properties: {}, required: [] }
      }
    },
    {
      type: "function",
      function: {
        name: "pushKnowledgeCard",
        description: "撰写并保存知识卡片",
        parameters: {
          type: "object",
          properties: {
            domainId: { type: "integer" },
            title: { type: "string" },
            summary: { type: "string" },
            detail: { type: "string" }
          },
          required: ["domainId", "title", "summary", "detail"]
        }
      }
    },
    {
      type: "function",
      function: {
        name: "skipPush",
        description: "跳过本次推送",
        parameters: {
          type: "object",
          properties: { reason: { type: "string" } },
          required: ["reason"]
        }
      }
    }
  ];
}

async function requestChat(input: {
  baseUrl: string;
  apiKey: string;
  model: string;
  messages: ChatMessage[];
  tools: unknown[];
}): Promise<{ content?: string; tool_calls?: Array<{ id: string; function: { name: string; arguments: string } }> }> {
  const res = await fetch(`${input.baseUrl}/chat/completions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${input.apiKey || "sk-placeholder"}`
    },
    body: JSON.stringify({
      model: input.model,
      messages: input.messages,
      tools: input.tools,
      temperature: 0.6,
      max_tokens: 1800
    })
  });
  if (!res.ok) {
    throw new Error(`模型请求失败: ${res.status}`);
  }
  const json = (await res.json()) as {
    choices?: Array<{
      message?: {
        content?: string;
        tool_calls?: Array<{ id: string; function: { name: string; arguments: string } }>;
      };
    }>;
  };
  const msg = json.choices?.[0]?.message;
  return { content: msg?.content, tool_calls: msg?.tool_calls };
}

async function executeTool(
  toolName: string,
  args: Record<string, unknown>,
  settings: Awaited<ReturnType<typeof getSettings>>
): Promise<string> {
  if (toolName === "readUserSettings") {
    return JSON.stringify(settings, null, 2);
  }
  if (toolName === "listDomains") {
    return JSON.stringify(await listDomains(), null, 2);
  }
  if (toolName === "readPushHistory") {
    const limit = normalizeInt(args.limit, 10);
    return JSON.stringify(await getRecentPushHistory(limit), null, 2);
  }
  if (toolName === "readUserFeedback") {
    const limit = normalizeInt(args.limit, 20);
    return JSON.stringify(await getUserFeedback(limit), null, 2);
  }
  if (toolName === "getDomainStats") {
    return JSON.stringify(await getDomainStats(), null, 2);
  }
  if (toolName === "pushKnowledgeCard") {
    const domains = (await listDomains()).filter((d) => d.is_enabled === 1);
    const target = resolveDomain(domains, normalizeInt(args.domainId, -1));
    const generated = await fallbackGenerationIfNeeded(args, settings, target);
    const created = await createKnowledgeCard({
      domainId: target?.id ?? null,
      domainName: target?.name ?? "未分类",
      title: generated.title,
      summary: generated.summary,
      detail: generated.detail
    });
    if (created.status === "duplicate") {
      return JSON.stringify({ status: "duplicate", message: "内容重复" });
    }
    return JSON.stringify({ status: "success", title: generated.title, itemId: created.itemId }, null, 2);
  }
  if (toolName === "skipPush") {
    return JSON.stringify({ status: "skipped", reason: String(args.reason || "无原因") }, null, 2);
  }
  return JSON.stringify({ error: `未知工具 ${toolName}` }, null, 2);
}

function resolveDomain(domains: Domain[], domainId: number): Domain | null {
  const matched = domains.find((d) => d.id === domainId);
  return matched ?? domains[0] ?? null;
}

async function fallbackGenerationIfNeeded(
  args: Record<string, unknown>,
  settings: Awaited<ReturnType<typeof getSettings>>,
  domain: Domain | null
): Promise<{ title: string; summary: string; detail: string }> {
  const title = String(args.title || "").trim();
  const summary = String(args.summary || "").trim();
  const detail = String(args.detail || "").trim();
  if (title && summary && detail) {
    return { title: title.slice(0, 20), summary: summary.slice(0, 60), detail };
  }
  return generateCard({
    baseUrl: settings.model_base_url,
    apiKey: settings.model_api_key,
    model: settings.model_name,
    userPreference: settings.user_preference_prompt,
    domainName: domain?.name ?? "未分类",
    domainKeywords: domain?.keywords ?? ""
  });
}

function normalizeInt(value: unknown, fallback: number): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function safeJsonParse<T>(raw: string, fallback: T): T {
  try {
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}
