import { useMemo, useState } from "react";
import type { AgentLog, AppSettings, DashboardStats, DomainStat, KnowledgeItem } from "../core/types";

type TimelineFilter = "all" | "thought" | "action" | "observation" | "final" | "error";

interface DashboardProps {
  stats: DashboardStats;
  settings: AppSettings;
  domainStats: DomainStat[];
  recentKnowledge: KnowledgeItem[];
  timeline: AgentLog[];
  timelineFilter: TimelineFilter;
  onTimelineFilterChange: (f: TimelineFilter) => void;
  expandedTimelineIds: number[];
  onToggleTimelineExpand: (id: number) => void;
  onOpenKnowledge: (itemId: number | null) => void;
  onClearTimeline: () => void;
}

const FILTER_OPTIONS: TimelineFilter[] = ["all", "thought", "action", "observation", "final", "error"];

const STEP_LABELS: Record<TimelineFilter, string> = {
  all: "全部",
  thought: "思考",
  action: "动作",
  observation: "观察",
  final: "结果",
  error: "错误"
};

export default function Dashboard({
  stats,
  settings,
  domainStats,
  recentKnowledge,
  timeline,
  timelineFilter,
  onTimelineFilterChange,
  expandedTimelineIds,
  onToggleTimelineExpand,
  onOpenKnowledge,
  onClearTimeline
}: DashboardProps) {
  const [clearingTimeline, setClearingTimeline] = useState(false);

  const filteredTimeline =
    timelineFilter === "all" ? timeline : timeline.filter((entry) => entry.step_type === timelineFilter);

  const timelineSummary = useMemo(() => {
    const sessions = new Set(timeline.map((e) => e.session_id));
    const errors = timeline.filter((e) => e.step_type === "error").length;
    const finals = timeline.filter((e) => e.step_type === "final").length;
    return { sessions: sessions.size, errors, finals };
  }, [timeline]);

  const domainMax = useMemo(
    () => Math.max(1, ...domainStats.map((row) => row.count)),
    [domainStats]
  );

  const topDomains = domainStats.slice(0, 6);

  return (
    <section className="panel-grid dashboard-grid">
      <section className="panel">
        <h3>推送计划</h3>
        <dl className="overview-list">
          <div>
            <dt>自动推送</dt>
            <dd>
              <span className={`status-pill${settings.push_enabled ? " on" : ""}`}>
                {settings.push_enabled ? "已开启" : "已关闭"}
              </span>
            </dd>
          </div>
          <div>
            <dt>推送间隔</dt>
            <dd>每 {settings.push_interval_minutes} 分钟</dd>
          </div>
          <div>
            <dt>推送时段</dt>
            <dd>
              {settings.push_start_hour}:00 – {settings.push_end_hour}:00
            </dd>
          </div>
          <div>
            <dt>模型</dt>
            <dd className="overview-mono" title={settings.model_name}>
              {settings.model_name || "未配置"}
            </dd>
          </div>
        </dl>
        <p className="overview-hint">
          {timelineSummary.sessions > 0
            ? `近期 ${timelineSummary.sessions} 次 Agent 会话，${timelineSummary.finals} 条结果、${timelineSummary.errors} 条错误`
            : "执行推送后，时间线会记录 Agent 决策过程"}
        </p>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <h3>领域分布</h3>
          <span className="panel-stat">{stats.domains} 个领域已启用</span>
        </div>
        {topDomains.length > 0 ? (
          <ul className="domain-bars">
            {topDomains.map((row) => (
              <li key={`${row.domain_id ?? "none"}-${row.domain_name}`}>
                <div className="domain-bar-head">
                  <span>{row.domain_name || "未分类"}</span>
                  <strong>{row.count}</strong>
                </div>
                <div className="domain-bar-track" aria-hidden>
                  <span
                    className="domain-bar-fill"
                    style={{ width: `${Math.round((row.count / domainMax) * 100)}%` }}
                  />
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <p className="empty">暂无知识，推送后将按领域统计</p>
        )}
      </section>

      <section className="panel dashboard-recent">
        <div className="panel-heading">
          <h3>最新知识</h3>
          <span className="panel-stat">共 {stats.total} 条</span>
        </div>
        <div className="mini-list">
          {recentKnowledge.map((item) => (
            <article key={item.id}>
              <button
                type="button"
                className="link-btn"
                onClick={() => onOpenKnowledge(item.id)}
              >
                {item.title}
              </button>
              <small>
                {item.domain_name || "未分类"} · {new Date(item.created_at).toLocaleString()}
              </small>
            </article>
          ))}
          {recentKnowledge.length === 0 && (
            <p className="empty">知识库为空，可通过侧栏「立即推送」生成</p>
          )}
        </div>
      </section>

      <section className="panel full">
        <div className="timeline-head">
          <h3>Agent 执行时间线</h3>
          <div className="timeline-head-actions">
            {clearingTimeline ? (
              <>
                <button type="button" className="ghost" onClick={() => setClearingTimeline(false)}>
                  取消
                </button>
                <button
                  type="button"
                  className="danger"
                  onClick={() => {
                    onClearTimeline();
                    setClearingTimeline(false);
                  }}
                >
                  确认清空
                </button>
              </>
            ) : (
              <button
                type="button"
                className="danger"
                disabled={timeline.length === 0}
                onClick={() => setClearingTimeline(true)}
              >
                清空记录
              </button>
            )}
            <div className="chip-row">
              {FILTER_OPTIONS.map((it) => (
                <button
                  key={it}
                  type="button"
                  className={timelineFilter === it ? "chip active" : "chip"}
                  onClick={() => onTimelineFilterChange(it)}
                >
                  {STEP_LABELS[it]}
                </button>
              ))}
            </div>
          </div>
        </div>
        <div className="timeline">
          {filteredTimeline.map((entry) => (
            <article key={entry.id} className={`timeline-item ${entry.step_type}`}>
              <div className="dot" />
              <div>
                <header>
                  <strong>{entry.step_type}</strong>
                  <small>{new Date(entry.created_at).toLocaleString()}</small>
                </header>
                <p>{entry.content ?? "无内容"}</p>
                {entry.tool_name && <small>工具: {entry.tool_name}</small>}
                {(entry.tool_input || entry.tool_output) && (
                  <div className="timeline-detail">
                    <button
                      type="button"
                      className="ghost"
                      onClick={() => onToggleTimelineExpand(entry.id)}
                    >
                      {expandedTimelineIds.includes(entry.id) ? "收起细节" : "展开细节"}
                    </button>
                    {expandedTimelineIds.includes(entry.id) && (
                      <div className="timeline-code">
                        {entry.tool_input && (
                          <>
                            <small>输入</small>
                            <pre>{entry.tool_input}</pre>
                          </>
                        )}
                        {entry.tool_output && (
                          <>
                            <small>输出</small>
                            <pre>{entry.tool_output}</pre>
                          </>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </article>
          ))}
          {filteredTimeline.length === 0 && <p className="empty">暂无执行日志</p>}
        </div>
      </section>
    </section>
  );
}
