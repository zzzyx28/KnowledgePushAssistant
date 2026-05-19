export interface Domain {
  id: number;
  name: string;
  description: string;
  keywords: string;
  sort_order: number;
  is_enabled: number;
}

export interface KnowledgeItem {
  id: number;
  domain_id: number | null;
  domain_name: string;
  title: string;
  summary: string;
  detail: string;
  source_url: string | null;
  source_title: string | null;
  trust_score: number;
  content_hash: string;
  is_read: number;
  is_favorited: number;
  rating: number | null;
  created_at: string;
}

export interface AppSettings {
  push_enabled: boolean;
  push_interval_minutes: number;
  push_start_hour: number;
  push_end_hour: number;
  model_name: string;
  model_base_url: string;
  model_api_key: string;
  user_preference_prompt: string;
}

export interface DashboardStats {
  total: number;
  recent7d: number;
  domains: number;
}

export interface DomainStat {
  domain_id: number | null;
  domain_name: string;
  count: number;
  avg_rating: number;
  last_push_at: string | null;
}

export type AgentStepType = "thought" | "action" | "observation" | "final" | "error";

export interface AgentLog {
  id: number;
  session_id: string;
  step_type: AgentStepType;
  tool_name: string | null;
  tool_input: string | null;
  tool_output: string | null;
  content: string | null;
  created_at: string;
}
