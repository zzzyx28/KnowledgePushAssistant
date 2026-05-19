import { useState } from "react";
import type { AppSettings } from "../core/types";

interface SettingsProps {
  settings: AppSettings;
  onChange: (v: AppSettings) => void;
  onSave: () => void;
  saving: boolean;
  onReset: () => void;
  resetting: boolean;
}

export default function Settings({ settings, onChange, onSave, saving, onReset, resetting }: SettingsProps) {
  const [confirmReset, setConfirmReset] = useState(false);

  return (
    <section className="panel settings-panel">
      <h3>设置中心</h3>
      <form
        className="form-grid settings-form"
        onSubmit={(e) => {
          e.preventDefault();
          onSave();
        }}
      >
        <label>
          模型名称
          <input
            type="text"
            value={settings.model_name}
            onChange={(e) => onChange({ ...settings, model_name: e.target.value })}
            placeholder="deepseek-chat"
            autoComplete="off"
          />
        </label>
        <label>
          Base URL
          <input
            type="url"
            value={settings.model_base_url}
            onChange={(e) => onChange({ ...settings, model_base_url: e.target.value })}
            placeholder="https://api.deepseek.com"
            autoComplete="off"
          />
        </label>
        <label className="span-2">
          API Key
          <input
            type="password"
            value={settings.model_api_key}
            onChange={(e) => onChange({ ...settings, model_api_key: e.target.value })}
            placeholder="sk-..."
            autoComplete="off"
          />
        </label>
        <div className="form-row-3 span-2">
          <label>
            推送间隔(分钟)
            <input
              type="number"
              min={5}
              value={settings.push_interval_minutes}
              onChange={(e) =>
                onChange({ ...settings, push_interval_minutes: Number(e.target.value) || 60 })
              }
            />
          </label>
          <label>
            开始小时
            <input
              type="number"
              min={0}
              max={23}
              value={settings.push_start_hour}
              onChange={(e) =>
                onChange({ ...settings, push_start_hour: Number(e.target.value) || 0 })
              }
            />
          </label>
          <label>
            结束小时
            <input
              type="number"
              min={0}
              max={23}
              value={settings.push_end_hour}
              onChange={(e) =>
                onChange({ ...settings, push_end_hour: Number(e.target.value) || 23 })
              }
            />
          </label>
        </div>
        <label className="span-2">
          用户偏好提示词
          <textarea
            rows={3}
            value={settings.user_preference_prompt}
            onChange={(e) =>
              onChange({ ...settings, user_preference_prompt: e.target.value })
            }
          />
        </label>
        <div className="form-actions span-2">
          <label className="inline">
            <input
              type="checkbox"
              checked={settings.push_enabled}
              onChange={(e) => onChange({ ...settings, push_enabled: e.target.checked })}
            />
            启用自动推送
          </label>
          <button className="primary" type="submit" disabled={saving}>
            {saving ? "保存中..." : "保存设置"}
          </button>
        </div>
      </form>

      <hr className="settings-divider" />

      <div className="settings-danger-zone">
        <h4>数据管理</h4>
        <p className="text-muted">
          初始化将清除所有知识点、推送历史和用户新增的领域，保留默认领域（计算机基础、人工智能）。
        </p>
        {confirmReset ? (
          <div className="confirm-row">
            <button type="button" className="ghost" onClick={() => setConfirmReset(false)}>
              取消
            </button>
            <button
              type="button"
              className="danger"
              disabled={resetting}
              onClick={() => {
                onReset();
                setConfirmReset(false);
              }}
            >
              {resetting ? "初始化中..." : "确认初始化"}
            </button>
          </div>
        ) : (
          <button type="button" className="danger" onClick={() => setConfirmReset(true)}>
            初始化数据
          </button>
        )}
      </div>
    </section>
  );
}
