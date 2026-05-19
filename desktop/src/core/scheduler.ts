import { getSettings } from "./repository";
import { runAgentOnce } from "./agent/service";

let timer: number | null = null;

export interface SchedulerResult {
  ok: boolean;
  message: string;
}

function isWithinWindow(currentHour: number, start: number, end: number): boolean {
  if (start <= end) {
    return currentHour >= start && currentHour < end;
  }
  return currentHour >= start || currentHour < end;
}

export async function startScheduler(): Promise<SchedulerResult> {
  await stopScheduler();
  const settings = await getSettings();
  if (!settings.push_enabled) {
    return { ok: false, message: "定时推送未启用，请先在设置中开启自动推送" };
  }

  const intervalMs = Math.max(settings.push_interval_minutes, 5) * 60 * 1000;
  timer = window.setInterval(async () => {
    try {
      const current = await getSettings();
      if (!current.push_enabled) return;

      const hour = new Date().getHours();
      if (!isWithinWindow(hour, current.push_start_hour, current.push_end_hour)) return;

      const result = await runAgentOnce();
      window.dispatchEvent(new CustomEvent("scheduler-tick", { detail: result.message }));
    } catch (error) {
      window.dispatchEvent(
        new CustomEvent("scheduler-tick", { detail: `定时推送失败: ${String(error)}` })
      );
    }
  }, intervalMs);

  return {
    ok: true,
    message: `定时推送已启动，间隔 ${settings.push_interval_minutes} 分钟`
  };
}

export async function stopScheduler(): Promise<SchedulerResult> {
  if (timer !== null) {
    window.clearInterval(timer);
    timer = null;
  }
  return { ok: true, message: "定时推送已停止" };
}

export function isSchedulerRunning(): boolean {
  return timer !== null;
}
