import { useCallback, useDeferredValue, useEffect, useMemo, useRef, useState } from "react";
import { listen } from "@tauri-apps/api/event";
import { invoke } from "@tauri-apps/api/core";
import {
  isPermissionGranted as isNotificationPermissionGranted,
  requestPermission as requestNotificationPermission,
  sendNotification
} from "@tauri-apps/plugin-notification";

import Sidebar from "./components/Sidebar";
import Dashboard from "./components/Dashboard";
import KnowledgeList from "./components/KnowledgeList";
import DomainManager from "./components/DomainManager";
import Settings from "./components/Settings";
import DetailOverlay from "./components/DetailOverlay";
import { MoonIcon, SunIcon } from "./components/icons";

import { runAgentOnce } from "./core/agent/service";
import {
  clearAgentLogs,
  deleteDomain,
  deleteKnowledgeItem,
  getDashboardStats,
  getKnowledgeById,
  getRecentAgentLogs,
  getDomainStats,
  getSettings,
  listDomains,
  listKnowledge,
  saveDomain,
  saveSettings
} from "./core/repository";
import { startScheduler, stopScheduler } from "./core/scheduler";
import { DEFAULT_SETTINGS } from "./core/defaults";
import type {
  AgentLog,
  AppSettings,
  DashboardStats,
  Domain,
  DomainStat,
  KnowledgeItem
} from "./core/types";

type TabKey = "dashboard" | "knowledge" | "domains" | "settings";
type TimelineFilter = "all" | "thought" | "action" | "observation" | "final" | "error";

export default function App() {
  const [tab, setTab] = useState<TabKey>("dashboard");
  const [domains, setDomains] = useState<Domain[]>([]);
  const [knowledge, setKnowledge] = useState<KnowledgeItem[]>([]);
  const [timeline, setTimeline] = useState<AgentLog[]>([]);
  const [domainStats, setDomainStats] = useState<DomainStat[]>([]);
  const [stats, setStats] = useState<DashboardStats>({ total: 0, recent7d: 0, domains: 0 });
  const [settings, setSettingsState] = useState<AppSettings>(DEFAULT_SETTINGS);
  const [searchInput, setSearchInput] = useState("");
  const deferredKeyword = useDeferredValue(searchInput);
  const [logs, setLogs] = useState<string[]>([]);
  const [detailItem, setDetailItem] = useState<KnowledgeItem | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const knowledgeRef = useRef(knowledge);
  knowledgeRef.current = knowledge;
  const [expandedTimelineIds, setExpandedTimelineIds] = useState<number[]>([]);
  const [timelineFilter, setTimelineFilter] = useState<TimelineFilter>("all");
  const [initialLoading, setInitialLoading] = useState(true);
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [isRunning, setIsRunning] = useState(false);
  const [savingSettings, setSavingSettings] = useState(false);
  const [toast, setToast] = useState<{ kind: "success" | "error"; text: string } | null>(null);

  const latestLog = useMemo(() => logs[0] ?? "系统就绪", [logs]);

  /* ---- data loading ---- */

  useEffect(() => {
    void refreshAll(true);
  }, []);

  useEffect(() => {
    void (async () => {
      const rows = await listKnowledge(deferredKeyword);
      setKnowledge(rows);
    })();
  }, [deferredKeyword]);

  useEffect(() => {
    if (!toast) return;
    const timer = window.setTimeout(() => setToast(null), 2200);
    return () => window.clearTimeout(timer);
  }, [toast]);

  /* ---- theme ---- */

  useEffect(() => {
    const savedTheme = localStorage.getItem("kpa-theme");
    if (savedTheme === "dark" || savedTheme === "light") {
      setTheme(savedTheme);
    }
  }, []);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("kpa-theme", theme);
  }, [theme]);

  /* ---- helper functions (stable across renders) ---- */

  function pushLog(message: string): void {
    setLogs((prev) => [`${new Date().toLocaleTimeString()} ${message}`, ...prev].slice(0, 40));
  }

  function pushToast(kind: "success" | "error", text: string): void {
    setToast({ kind, text });
  }

  useEffect(() => {
    const onSchedulerTick = (event: Event) => {
      const message = (event as CustomEvent<string>).detail;
      pushLog(message);
    };
    window.addEventListener("scheduler-tick", onSchedulerTick);
    return () => window.removeEventListener("scheduler-tick", onSchedulerTick);
  }, []);

  async function refreshAll(showLoading = false): Promise<void> {
    if (showLoading) setInitialLoading(true);
    try {
      const [domainRows, knowledgeRows, statRows, settingRows, timelineRows, domainStatRows] =
        await Promise.all([
          listDomains(),
          listKnowledge(),
          getDashboardStats(),
          getSettings(),
          getRecentAgentLogs(),
          getDomainStats()
        ]);
      setDomains(domainRows);
      setKnowledge(knowledgeRows);
      setStats(statRows);
      setSettingsState(settingRows);
      setTimeline(timelineRows);
      setDomainStats(domainStatRows);
    } finally {
      if (showLoading) setInitialLoading(false);
    }
  }

  async function refreshDomains(): Promise<void> {
    const [domainRows, statRows] = await Promise.all([listDomains(), getDashboardStats()]);
    setDomains(domainRows);
    setStats(statRows);
  }

  async function handleRunAgent(): Promise<void> {
    setIsRunning(true);
    try {
      const result = await runAgentOnce();
      pushLog(result.message);
      pushToast(result.ok ? "success" : "error", result.message);
      await refreshAll();
      if (result.ok && result.pushedItemId) {
        const pushed = await getKnowledgeById(result.pushedItemId);
        try {
          await invoke("set_latest_pushed_item", { itemId: result.pushedItemId });
        } catch (trayError) {
          pushLog(`托盘状态更新失败: ${String(trayError)}`);
        }
        if (pushed) await notifyKnowledgePushed(pushed);
      }
    } catch (error) {
      pushLog(`执行失败: ${String(error)}`);
      pushToast("error", `执行失败: ${String(error)}`);
    } finally {
      setIsRunning(false);
    }
  }

  const openKnowledgeDetail = useCallback((item: KnowledgeItem) => {
    setDetailItem(item);
    setDetailLoading(false);
    requestAnimationFrame(() => setDetailOpen(true));
  }, []);

  const closeKnowledgeDetail = useCallback(() => {
    setDetailOpen(false);
  }, []);

  const handleDetailExited = useCallback(() => {
    setDetailItem(null);
    setDetailLoading(false);
  }, []);

  async function openKnowledgeById(itemId: number | null): Promise<void> {
    if (!itemId) return;
    const cached = knowledgeRef.current.find((row) => row.id === itemId);
    if (cached) {
      openKnowledgeDetail(cached);
    } else {
      setDetailItem(null);
      setDetailLoading(true);
      setDetailOpen(true);
    }
    const detail = await getKnowledgeById(itemId);
    if (detail) {
      openKnowledgeDetail(detail);
    } else if (!cached) {
      closeKnowledgeDetail();
    }
  }

  async function notifyKnowledgePushed(item: KnowledgeItem): Promise<void> {
    let granted = await isNotificationPermissionGranted();
    if (!granted) {
      const permission = await requestNotificationPermission();
      granted = permission === "granted";
    }
    if (!granted) return;
    sendNotification({
      title: "Knowledge Push Assistant",
      body: `已推送：${item.title}\n可从托盘菜单"打开最新推送"查看详情`
    });
  }

  /* ---- stable refs for tray event listeners ---- */

  const handleRunAgentRef = useRef(handleRunAgent);
  handleRunAgentRef.current = handleRunAgent;
  const openKnowledgeByIdRef = useRef(openKnowledgeById);
  openKnowledgeByIdRef.current = openKnowledgeById;

  /* ---- tray event listeners ---- */

  useEffect(() => {
    let unlistenPushNow: (() => void) | null = null;
    let unlistenOpenLatest: (() => void) | null = null;

    void (async () => {
      unlistenPushNow = await listen("tray-push-now", () => {
        void handleRunAgentRef.current();
      });
      unlistenOpenLatest = await listen("tray-open-latest", async () => {
        try {
          const latestId = await invoke<number | null>("get_latest_pushed_item");
          if (latestId) {
            setTab("knowledge");
            await openKnowledgeByIdRef.current(latestId);
          }
        } catch (error) {
          pushToast("error", `打开最新推送失败: ${String(error)}`);
        }
      });
    })();

    return () => {
      if (unlistenPushNow) unlistenPushNow();
      if (unlistenOpenLatest) unlistenOpenLatest();
    };
  }, []);

  /* ---- action handlers ---- */

  async function handleSaveSettings(): Promise<void> {
    setSavingSettings(true);
    try {
      await saveSettings(settings);
      pushLog("设置已保存");
      pushToast("success", "设置已保存");
      const sched = await stopScheduler();
      pushLog(sched.message);
      const started = await startScheduler();
      pushLog(started.message);
      pushToast(started.ok ? "success" : "error", started.message);
    } finally {
      setSavingSettings(false);
    }
  }

  async function handleAddDomain(form: {
    name: string;
    description: string;
    keywords: string;
  }): Promise<void> {
    if (!form.name.trim()) return;
    await saveDomain({
      name: form.name.trim(),
      description: form.description,
      keywords: form.keywords,
      is_enabled: 1,
      sort_order: 0
    });
    await refreshDomains();
    pushToast("success", "领域已新增");
  }

  async function handleUpdateDomain(domain: Domain): Promise<void> {
    await saveDomain(domain);
    await refreshDomains();
    pushToast("success", "领域已更新");
  }

  async function handleDeleteDomain(id: number): Promise<void> {
    await deleteDomain(id);
    await refreshDomains();
    pushToast("success", "领域已删除");
  }

  async function handleToggleDomain(domain: Domain): Promise<void> {
    const nextEnabled = domain.is_enabled === 1 ? 0 : 1;
    const snapshot = domains;
    setDomains((prev) =>
      prev.map((d) => (d.id === domain.id ? { ...d, is_enabled: nextEnabled } : d))
    );
    try {
      await saveDomain({ ...domain, is_enabled: nextEnabled });
      pushToast("success", nextEnabled === 1 ? "已启用" : "已禁用");
    } catch (error) {
      setDomains(snapshot);
      pushToast("error", `操作失败: ${String(error)}`);
    }
  }

  function toggleTimelineExpand(id: number): void {
    setExpandedTimelineIds((prev) => (prev.includes(id) ? prev.filter((n) => n !== id) : [...prev, id]));
  }

  async function refreshKnowledgeViews(): Promise<void> {
    const [knowledgeRows, statRows, domainStatRows] = await Promise.all([
      listKnowledge(deferredKeyword),
      getDashboardStats(),
      getDomainStats()
    ]);
    setKnowledge(knowledgeRows);
    setStats(statRows);
    setDomainStats(domainStatRows);
  }

  async function handleDeleteKnowledge(itemId: number): Promise<void> {
    try {
      await deleteKnowledgeItem(itemId);
      if (detailItem?.id === itemId) {
        setDetailOpen(false);
        setDetailItem(null);
        setDetailLoading(false);
      }
      setExpandedTimelineIds([]);
      await Promise.all([refreshKnowledgeViews(), getRecentAgentLogs().then(setTimeline)]);
      pushToast("success", "知识已删除");
    } catch (error) {
      pushToast("error", `删除失败: ${String(error)}`);
    }
  }

  async function handleClearAgentLogs(): Promise<void> {
    try {
      await clearAgentLogs();
      setTimeline([]);
      setExpandedTimelineIds([]);
      pushToast("success", "时间线已清空");
    } catch (error) {
      pushToast("error", `清空失败: ${String(error)}`);
    }
  }

  /* ---- render ---- */

  return (
    <div className="app-shell">
      {toast && <div className={`toast ${toast.kind}`}>{toast.text}</div>}

      <Sidebar
        tab={tab}
        onTabChange={(key) => setTab(key as TabKey)}
        isRunning={isRunning}
        onRunAgent={() => { void handleRunAgent(); }}
        onStartScheduler={async () => {
          try {
            const result = await startScheduler();
            pushLog(result.message);
            pushToast(result.ok ? "success" : "error", result.message);
          } catch (error) {
            pushLog(`启动定时器失败: ${String(error)}`);
            pushToast("error", `启动失败: ${String(error)}`);
          }
        }}
        onStopScheduler={async () => {
          try {
            const result = await stopScheduler();
            pushLog(result.message);
            pushToast(result.ok ? "success" : "error", result.message);
          } catch (error) {
            pushLog(`停止定时器失败: ${String(error)}`);
            pushToast("error", `停止失败: ${String(error)}`);
          }
        }}
        latestLog={latestLog}
      />

      <main className="content">
        <header className="hero">
          <div>
            <h2>智能知识推送工作台</h2>
            <p>统一管理推送计划、领域配置和知识内容，支持 Agent 决策全链路追踪。</p>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span className="status-chip">{latestLog}</span>
            <button
              type="button"
              className="ghost theme-toggle"
              onClick={() => setTheme((prev) => (prev === "light" ? "dark" : "light"))}
              aria-label="切换主题"
            >
              {theme === "light" ? <MoonIcon /> : <SunIcon />}
            </button>
          </div>
        </header>

        {initialLoading && <section className="panel loading">数据加载中...</section>}

        {!initialLoading && tab === "dashboard" && (
          <Dashboard
            stats={stats}
            settings={settings}
            domainStats={domainStats}
            recentKnowledge={knowledge.slice(0, 6)}
            timeline={timeline}
            timelineFilter={timelineFilter}
            onTimelineFilterChange={setTimelineFilter}
            expandedTimelineIds={expandedTimelineIds}
            onToggleTimelineExpand={toggleTimelineExpand}
            onOpenKnowledge={(id) => { void openKnowledgeById(id); }}
            onClearTimeline={() => { void handleClearAgentLogs(); }}
          />
        )}

        {!initialLoading && tab === "knowledge" && (
          <KnowledgeList
            knowledge={knowledge}
            searchInput={searchInput}
            onSearchChange={setSearchInput}
            onSelectItem={openKnowledgeDetail}
            onDeleteItem={(id) => { void handleDeleteKnowledge(id); }}
          />
        )}

        {!initialLoading && tab === "domains" && (
          <DomainManager
            domains={domains}
            onAddDomain={(form) => { void handleAddDomain(form); }}
            onUpdateDomain={(d) => { void handleUpdateDomain(d); }}
            onToggleDomain={(d) => { void handleToggleDomain(d); }}
            onDeleteDomain={(id) => { void handleDeleteDomain(id); }}
          />
        )}

        {!initialLoading && tab === "settings" && (
          <Settings
            settings={settings}
            onChange={setSettingsState}
            onSave={() => { void handleSaveSettings(); }}
            saving={savingSettings}
          />
        )}
      </main>

      {(detailItem || detailOpen || detailLoading) && (
        <DetailOverlay
          open={detailOpen}
          item={detailItem}
          loading={detailLoading}
          settings={settings}
          onClose={closeKnowledgeDetail}
          onExited={handleDetailExited}
        />
      )}
    </div>
  );
}
