import Database from "@tauri-apps/plugin-sql";
import { DEFAULT_DOMAINS, DEFAULT_SETTINGS } from "./defaults";

let dbPromise: Promise<Database> | null = null;

export async function getDb(): Promise<Database> {
  if (!dbPromise) {
    dbPromise = initDatabase().catch((error) => {
      dbPromise = null;
      throw error;
    });
  }
  return dbPromise;
}

async function initDatabase(): Promise<Database> {
  const database = await Database.load("sqlite:kpa.db");
  await initSchema(database);
  await seedDefaults(database);
  return database;
}

async function initSchema(database: Database): Promise<void> {
  await database.execute(`
    CREATE TABLE IF NOT EXISTS knowledge_domains (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      description TEXT DEFAULT '',
      keywords TEXT DEFAULT '',
      sort_order INTEGER DEFAULT 0,
      is_enabled INTEGER DEFAULT 1
    )
  `);

  await database.execute(`
    CREATE TABLE IF NOT EXISTS knowledge_items (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      domain_id INTEGER,
      domain_name TEXT DEFAULT '',
      title TEXT NOT NULL,
      summary TEXT DEFAULT '',
      detail TEXT DEFAULT '',
      source_url TEXT,
      source_title TEXT,
      trust_score REAL DEFAULT 0.5,
      content_hash TEXT UNIQUE NOT NULL,
      is_read INTEGER DEFAULT 0,
      is_favorited INTEGER DEFAULT 0,
      rating INTEGER,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
  `);

  await database.execute(`
    CREATE TABLE IF NOT EXISTS push_history (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      knowledge_item_id INTEGER,
      pushed_at TEXT DEFAULT CURRENT_TIMESTAMP,
      is_clicked INTEGER DEFAULT 0
    )
  `);

  await database.execute(`
    CREATE TABLE IF NOT EXISTS user_settings (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      key TEXT UNIQUE NOT NULL,
      value TEXT DEFAULT ''
    )
  `);

  await database.execute(`
    CREATE TABLE IF NOT EXISTS agent_execution_logs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      session_id TEXT NOT NULL,
      step_type TEXT NOT NULL,
      tool_name TEXT,
      tool_input TEXT,
      tool_output TEXT,
      content TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
  `);
}

async function seedDefaults(database: Database): Promise<void> {
  const domainCount = await database.select<{ count: number }[]>(
    "SELECT COUNT(*) as count FROM knowledge_domains"
  );
  if (domainCount[0]?.count === 0) {
    for (let i = 0; i < DEFAULT_DOMAINS.length; i += 1) {
      const d = DEFAULT_DOMAINS[i];
      await database.execute(
        "INSERT INTO knowledge_domains (name, description, keywords, sort_order, is_enabled) VALUES (?, ?, ?, ?, 1)",
        [d.name, d.description, d.keywords, i]
      );
    }
  }

  const settingCount = await database.select<{ count: number }[]>(
    "SELECT COUNT(*) as count FROM user_settings"
  );
  if (settingCount[0]?.count === 0) {
    for (const [key, value] of Object.entries(DEFAULT_SETTINGS)) {
      await database.execute(
        "INSERT INTO user_settings (key, value) VALUES (?, ?)",
        [key, JSON.stringify(value)]
      );
    }
  }
}
