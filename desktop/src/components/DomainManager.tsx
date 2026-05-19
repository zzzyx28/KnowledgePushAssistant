import { useState } from "react";
import type { Domain } from "../core/types";

interface DomainForm {
  name: string;
  description: string;
  keywords: string;
}

interface DomainManagerProps {
  domains: Domain[];
  onAddDomain: (form: DomainForm) => void;
  onUpdateDomain: (domain: Domain) => void;
  onToggleDomain: (domain: Domain) => void;
  onDeleteDomain: (id: number) => void;
}

export default function DomainManager({
  domains,
  onAddDomain,
  onUpdateDomain,
  onToggleDomain,
  onDeleteDomain
}: DomainManagerProps) {
  const [showAddForm, setShowAddForm] = useState(false);
  const [form, setForm] = useState<DomainForm>({ name: "", description: "", keywords: "" });
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState<DomainForm>({ name: "", description: "", keywords: "" });
  const [deletingId, setDeletingId] = useState<number | null>(null);

  function handleSubmit(e: React.FormEvent): void {
    e.preventDefault();
    if (!form.name.trim()) return;
    onAddDomain(form);
    setForm({ name: "", description: "", keywords: "" });
    setShowAddForm(false);
  }

  function startEdit(d: Domain): void {
    setEditingId(d.id);
    setEditForm({ name: d.name, description: d.description, keywords: d.keywords });
    setShowAddForm(false);
  }

  function cancelEdit(): void {
    setEditingId(null);
  }

  function handleEditSubmit(e: React.FormEvent, domain: Domain): void {
    e.preventDefault();
    if (!editForm.name.trim()) return;
    onUpdateDomain({ ...domain, ...editForm });
    setEditingId(null);
  }

  return (
    <section className="panel">
      <div className="panel-toolbar">
        <h3>领域管理</h3>
        <button
          type="button"
          className="primary"
          onClick={() => { setShowAddForm((v) => !v); setEditingId(null); }}
        >
          {showAddForm ? "取消" : "新增领域"}
        </button>
      </div>

      {showAddForm && (
        <form className="form-grid add-domain-form" onSubmit={handleSubmit}>
          <label>
            名称
            <input
              type="text"
              required
              autoFocus
              value={form.name}
              onChange={(e) => setForm((v) => ({ ...v, name: e.target.value }))}
              placeholder="例如：系统设计"
            />
          </label>
          <label className="span-2">
            描述
            <input
              type="text"
              value={form.description}
              onChange={(e) => setForm((v) => ({ ...v, description: e.target.value }))}
              placeholder="该领域包含哪些知识方向"
            />
          </label>
          <label className="span-2">
            关键词
            <input
              type="text"
              value={form.keywords}
              onChange={(e) => setForm((v) => ({ ...v, keywords: e.target.value }))}
              placeholder="多个关键词用空格分隔"
            />
          </label>
          <button className="primary span-2" type="submit">
            确认新增
          </button>
        </form>
      )}

      <div className="domain-list">
        {domains.map((d) =>
          editingId === d.id ? (
            <form
              key={d.id}
              className="form-grid add-domain-form"
              onSubmit={(e) => handleEditSubmit(e, d)}
            >
              <label>
                名称
                <input
                  type="text"
                  required
                  autoFocus
                  value={editForm.name}
                  onChange={(e) => setEditForm((v) => ({ ...v, name: e.target.value }))}
                />
              </label>
              <label className="span-2">
                描述
                <input
                  type="text"
                  value={editForm.description}
                  onChange={(e) => setEditForm((v) => ({ ...v, description: e.target.value }))}
                />
              </label>
              <label className="span-2">
                关键词
                <input
                  type="text"
                  value={editForm.keywords}
                  onChange={(e) => setEditForm((v) => ({ ...v, keywords: e.target.value }))}
                />
              </label>
              <div className="row">
                <button className="primary" type="submit">保存</button>
                <button type="button" onClick={cancelEdit}>取消</button>
              </div>
            </form>
          ) : (
            <article key={d.id} className="domain-card">
              <header>
                <h4>{d.name}</h4>
                <span className={d.is_enabled === 1 ? "enabled" : "disabled"}>
                  {d.is_enabled === 1 ? "已启用" : "已禁用"}
                </span>
              </header>
              <p>{d.description || "暂无描述"}</p>
              {d.keywords && <small className="domain-keywords">{d.keywords}</small>}
              <div className="row">
                <button type="button" onClick={() => onToggleDomain(d)}>
                  {d.is_enabled === 1 ? "禁用" : "启用"}
                </button>
                <button type="button" onClick={() => startEdit(d)}>
                  编辑
                </button>
                {deletingId === d.id ? (
                  <>
                    <button type="button" className="danger" onClick={() => { onDeleteDomain(d.id); setDeletingId(null); }}>
                      确认删除
                    </button>
                    <button type="button" onClick={() => setDeletingId(null)}>
                      取消
                    </button>
                  </>
                ) : (
                  <button type="button" className="danger" onClick={() => setDeletingId(d.id)}>
                    删除
                  </button>
                )}
              </div>
            </article>
          )
        )}
        {domains.length === 0 && <p className="empty">暂无领域，点击「新增领域」开始配置</p>}
      </div>
    </section>
  );
}
