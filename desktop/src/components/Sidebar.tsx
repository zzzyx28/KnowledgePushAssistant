import { ClockIcon, HomeIcon, LayersIcon, LibraryIcon, SettingsIcon, SparkIcon, StopIcon } from "./icons";

interface SidebarProps {
  tab: string;
  onTabChange: (key: string) => void;
  isRunning: boolean;
  onRunAgent: () => void;
  onStartScheduler: () => void;
  onStopScheduler: () => void;
  latestLog: string;
}

export default function Sidebar({
  tab,
  onTabChange,
  isRunning,
  onRunAgent,
  onStartScheduler,
  onStopScheduler,
  latestLog
}: SidebarProps) {
  const tabs: Array<{ key: string; label: string; icon: JSX.Element }> = [
    { key: "dashboard", label: "总览", icon: <HomeIcon /> },
    { key: "knowledge", label: "知识库", icon: <LibraryIcon /> },
    { key: "domains", label: "领域", icon: <LayersIcon /> },
    { key: "settings", label: "设置", icon: <SettingsIcon /> }
  ];

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">
          <SparkIcon />
        </div>
        <div>
          <h1>Knowledge Push</h1>
          <p>Tauri 2 Desktop</p>
        </div>
      </div>
      <nav className="nav-list" aria-label="主导航">
        {tabs.map((item) => (
          <button key={item.key} className={tab === item.key ? "active" : ""} onClick={() => onTabChange(item.key)}>
            {item.icon}
            <span>{item.label}</span>
          </button>
        ))}
      </nav>
      <div className="sidebar-actions">
        <button className="primary" onClick={onRunAgent} disabled={isRunning}>
          <SparkIcon />
          {isRunning ? "推送中..." : "立即推送"}
        </button>
        <button onClick={onStartScheduler}>
          <ClockIcon />
          启动定时器
        </button>
        <button onClick={onStopScheduler}>
          <StopIcon />
          停止定时器
        </button>
      </div>
    </aside>
  );
}
