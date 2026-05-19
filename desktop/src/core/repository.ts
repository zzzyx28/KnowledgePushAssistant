import { getDb } from "./db";
import { DEFAULT_DOMAINS, DEFAULT_SETTINGS } from "./defaults";
import type { AgentLog, AppSettings, DashboardStats, Domain, DomainStat, KnowledgeItem } from "./types";

export async function listDomains(): Promise<Domain[]> {
  const db = await getDb();
  return db.select<Domain[]>(
    "SELECT id, name, description, keywords, sort_order, is_enabled FROM knowledge_domains ORDER BY sort_order ASC, id ASC"
  );
}

export async function saveDomain(input: Partial<Domain> & Pick<Domain, "name">): Promise<void> {
  const db = await getDb();
  if (input.id) {
    await db.execute(
      "UPDATE knowledge_domains SET name = ?, description = ?, keywords = ?, is_enabled = ? WHERE id = ?",
      [input.name, input.description ?? "", input.keywords ?? "", input.is_enabled ?? 1, input.id]
    );
    return;
  }
  await db.execute(
    "INSERT INTO knowledge_domains (name, description, keywords, sort_order, is_enabled) VALUES (?, ?, ?, COALESCE((SELECT MAX(sort_order) + 1 FROM knowledge_domains), 0), ?)",
    [input.name, input.description ?? "", input.keywords ?? "", input.is_enabled ?? 1]
  );
}

export async function deleteDomain(domainId: number): Promise<void> {
  const db = await getDb();
  await db.execute("DELETE FROM knowledge_domains WHERE id = ?", [domainId]);
}

export async function listKnowledge(keyword = ""): Promise<KnowledgeItem[]> {
  const db = await getDb();
  if (!keyword.trim()) {
    return db.select<KnowledgeItem[]>(
      "SELECT * FROM knowledge_items ORDER BY datetime(created_at) DESC LIMIT 100"
    );
  }
  const like = `%${keyword.trim()}%`;
  return db.select<KnowledgeItem[]>(
    "SELECT * FROM knowledge_items WHERE title LIKE ? OR summary LIKE ? OR detail LIKE ? ORDER BY datetime(created_at) DESC LIMIT 100",
    [like, like, like]
  );
}

export async function getKnowledgeById(itemId: number): Promise<KnowledgeItem | null> {
  const db = await getDb();
  const rows = await db.select<KnowledgeItem[]>(
    "SELECT * FROM knowledge_items WHERE id = ? LIMIT 1",
    [itemId]
  );
  return rows[0] ?? null;
}

export async function toggleFavorite(itemId: number): Promise<{ is_favorited: boolean }> {
  const db = await getDb();
  const rows = await db.select<{ is_favorited: number }[]>(
    "SELECT is_favorited FROM knowledge_items WHERE id = ? LIMIT 1",
    [itemId]
  );
  if (rows.length === 0) {
    return { is_favorited: false };
  }
  const next = rows[0].is_favorited === 1 ? 0 : 1;
  const newRating = next === 1 ? 5 : null;
  await db.execute(
    "UPDATE knowledge_items SET is_favorited = ?, rating = ? WHERE id = ?",
    [next, newRating, itemId]
  );
  return { is_favorited: next === 1 };
}

export async function deleteKnowledgeItem(itemId: number): Promise<void> {
  const db = await getDb();
  await db.execute("DELETE FROM push_history WHERE knowledge_item_id = ?", [itemId]);
  await db.execute("DELETE FROM knowledge_items WHERE id = ?", [itemId]);
}

export async function clearAgentLogs(): Promise<void> {
  const db = await getDb();
  await db.execute("DELETE FROM agent_execution_logs");
}

export async function createKnowledgeCard(input: {
  domainId: number | null;
  domainName: string;
  title: string;
  summary: string;
  detail: string;
  sourceUrl?: string;
  sourceTitle?: string;
}): Promise<{ status: "created"; itemId: number } | { status: "duplicate" }> {
  const db = await getDb();
  const hash = await sha256(`${input.title}|${input.summary}|${input.detail}`);
  const exists = await db.select<{ id: number }[]>(
    "SELECT id FROM knowledge_items WHERE content_hash = ? LIMIT 1",
    [hash]
  );
  if (exists.length > 0) {
    return { status: "duplicate" };
  }
  const result = await db.execute(
    "INSERT INTO knowledge_items (domain_id, domain_name, title, summary, detail, source_url, source_title, trust_score, content_hash) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
    [
      input.domainId,
      input.domainName,
      input.title,
      input.summary,
      input.detail,
      input.sourceUrl ?? null,
      input.sourceTitle ?? null,
      0.5,
      hash
    ]
  );
  const itemId = result.lastInsertId;
  if (itemId) {
    await db.execute("INSERT INTO push_history (knowledge_item_id) VALUES (?)", [itemId]);
    return { status: "created", itemId };
  }
  return { status: "duplicate" };
}

export async function getSettings(): Promise<AppSettings> {
  const db = await getDb();
  const rows = await db.select<{ key: string; value: string }[]>(
    "SELECT key, value FROM user_settings"
  );
  const map: Record<string, unknown> = { ...DEFAULT_SETTINGS };
  for (const row of rows) {
    try {
      map[row.key] = JSON.parse(row.value);
    } catch {
      map[row.key] = row.value;
    }
  }
  return map as unknown as AppSettings;
}

export async function saveSettings(settings: AppSettings): Promise<void> {
  const db = await getDb();
  for (const [key, value] of Object.entries(settings)) {
    await db.execute(
      "INSERT INTO user_settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
      [key, JSON.stringify(value)]
    );
  }
}

export async function getDashboardStats(): Promise<DashboardStats> {
  const db = await getDb();
  const total = await db.select<{ count: number }[]>("SELECT COUNT(*) as count FROM knowledge_items");
  const recent7d = await db.select<{ count: number }[]>(
    "SELECT COUNT(*) as count FROM knowledge_items WHERE datetime(created_at) >= datetime('now', '-7 day')"
  );
  const domains = await db.select<{ count: number }[]>(
    "SELECT COUNT(*) as count FROM knowledge_domains WHERE is_enabled = 1"
  );
  return {
    total: total[0]?.count ?? 0,
    recent7d: recent7d[0]?.count ?? 0,
    domains: domains[0]?.count ?? 0
  };
}

export async function saveAgentLog(input: {
  sessionId: string;
  stepType: AgentLog["step_type"];
  content?: string;
  toolName?: string;
  toolInput?: string;
  toolOutput?: string;
}): Promise<void> {
  const db = await getDb();
  await db.execute(
    "INSERT INTO agent_execution_logs (session_id, step_type, tool_name, tool_input, tool_output, content) VALUES (?, ?, ?, ?, ?, ?)",
    [
      input.sessionId,
      input.stepType,
      input.toolName ?? null,
      input.toolInput ?? null,
      input.toolOutput ?? null,
      input.content ?? null
    ]
  );
}

export async function getRecentAgentLogs(limit = 50): Promise<AgentLog[]> {
  const db = await getDb();
  return db.select<AgentLog[]>(
    "SELECT * FROM agent_execution_logs ORDER BY id DESC LIMIT ?",
    [limit]
  );
}

export async function getRecentPushHistory(
  limit = 15
): Promise<Array<{ id: number; knowledge_item_id: number; pushed_at: string; title: string; domain_name: string; summary: string }>> {
  const db = await getDb();
  return db.select<Array<{ id: number; knowledge_item_id: number; pushed_at: string; title: string; domain_name: string; summary: string }>>(
    `SELECT ph.id, ph.knowledge_item_id, ph.pushed_at, ki.title, ki.domain_name, ki.summary
     FROM push_history ph
     INNER JOIN knowledge_items ki ON ki.id = ph.knowledge_item_id
     ORDER BY ph.pushed_at DESC
     LIMIT ?`,
    [limit]
  );
}

export async function getDomainStats(): Promise<DomainStat[]> {
  const db = await getDb();
  return db.select<DomainStat[]>(
    `SELECT
      ki.domain_id,
      COALESCE(ki.domain_name, '') as domain_name,
      COUNT(*) as count,
      COALESCE(ROUND(AVG(ki.rating), 1), 0) as avg_rating,
      MAX(ph.pushed_at) as last_push_at
    FROM knowledge_items ki
    LEFT JOIN push_history ph ON ph.knowledge_item_id = ki.id
    GROUP BY ki.domain_id, ki.domain_name
    ORDER BY last_push_at ASC NULLS FIRST`
  );
}

export async function getPushSummary(): Promise<
  Array<{
    domain_id: number | null;
    domain_name: string;
    total_pushes: number;
    last_push_at: string | null;
    last_title: string | null;
    hours_since_last: number | null;
  }>
> {
  const db = await getDb();
  return db.select<
    Array<{
      domain_id: number | null;
      domain_name: string;
      total_pushes: number;
      last_push_at: string | null;
      last_title: string | null;
      hours_since_last: number | null;
    }>
  >(
    `SELECT
       d.id as domain_id,
       d.name as domain_name,
       COUNT(ph.id) as total_pushes,
       MAX(ph.pushed_at) as last_push_at,
       (SELECT ki2.title FROM push_history ph2
        INNER JOIN knowledge_items ki2 ON ki2.id = ph2.knowledge_item_id
        WHERE ki2.domain_id = d.id
        ORDER BY ph2.id DESC LIMIT 1) as last_title,
       CAST(ROUND((JULIANDAY('now') - JULIANDAY(MAX(ph.pushed_at))) * 24) AS INTEGER) as hours_since_last
     FROM knowledge_domains d
     LEFT JOIN knowledge_items ki ON ki.domain_id = d.id
     LEFT JOIN push_history ph ON ph.knowledge_item_id = ki.id
     WHERE d.is_enabled = 1
     GROUP BY d.id, d.name
     ORDER BY hours_since_last DESC NULLS FIRST`
  );
}

export async function getUserFeedback(
  limit = 20
): Promise<Array<{ domain_name: string; title: string; rating: number | null; is_favorited: number }>> {
  const db = await getDb();
  return db.select<Array<{ domain_name: string; title: string; rating: number | null; is_favorited: number }>>(
    `SELECT
      COALESCE(domain_name, '') as domain_name,
      title,
      rating,
      is_favorited
    FROM knowledge_items
    WHERE rating IS NOT NULL
    ORDER BY datetime(created_at) DESC
    LIMIT ?`,
    [limit]
  );
}

export async function cleanOrphanedPushHistory(): Promise<number> {
  const db = await getDb();
  const result = await db.execute(
    "DELETE FROM push_history WHERE knowledge_item_id NOT IN (SELECT id FROM knowledge_items)"
  );
  return result.rowsAffected;
}

export async function resetAllData(): Promise<void> {
  const db = await getDb();
  await db.execute("DELETE FROM push_history");
  await db.execute("DELETE FROM knowledge_items");
  await db.execute("DELETE FROM agent_execution_logs");
  await db.execute(
    "DELETE FROM knowledge_domains WHERE name NOT IN (?, ?)",
    [DEFAULT_DOMAINS[0].name, DEFAULT_DOMAINS[1].name]
  );
  for (const d of DEFAULT_DOMAINS) {
    const exists = await db.select<{ count: number }[]>(
      "SELECT COUNT(*) as count FROM knowledge_domains WHERE name = ?",
      [d.name]
    );
    if (exists[0]?.count === 0) {
      await db.execute(
        "INSERT INTO knowledge_domains (name, description, keywords, sort_order, is_enabled) VALUES (?, ?, ?, ?, 1)",
        [d.name, d.description, d.keywords, DEFAULT_DOMAINS.indexOf(d)]
      );
    }
  }
}

async function sha256(raw: string): Promise<string> {
  const data = new TextEncoder().encode(raw);
  const digest = await crypto.subtle.digest("SHA-256", data);
  return Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}
