import { useState } from "react";
import type { KnowledgeItem } from "../core/types";
import { ThumbUpIcon } from "./icons";

interface KnowledgeListProps {
  knowledge: KnowledgeItem[];
  searchInput: string;
  onSearchChange: (value: string) => void;
  onSelectItem: (item: KnowledgeItem) => void;
  onDeleteItem: (itemId: number) => void;
  onToggleFavorite: (itemId: number) => void;
}

export default function KnowledgeList({
  knowledge,
  searchInput,
  onSearchChange,
  onSelectItem,
  onDeleteItem,
  onToggleFavorite
}: KnowledgeListProps) {
  const [deletingId, setDeletingId] = useState<number | null>(null);

  return (
    <section className="panel">
      <h3>知识库</h3>
      <div className="search-field">
        <label className="sr-only" htmlFor="knowledge-search">
          搜索知识
        </label>
        <input
          id="knowledge-search"
          type="search"
          value={searchInput}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="输入关键词实时检索标题 / 摘要 / 详情"
          autoComplete="off"
        />
      </div>
      <div className="knowledge-grid">
        {knowledge.map((item) => (
          <article key={item.id} className="knowledge-card">
            <header>
              <h4>{item.title}</h4>
              <span>{item.domain_name}</span>
            </header>
            <p>{item.summary}</p>
            <div className="card-actions">
              <button
                type="button"
                className={`ghost like-btn${item.is_favorited === 1 ? " is-liked" : ""}`}
                onClick={(e) => {
                  e.stopPropagation();
                  onToggleFavorite(item.id);
                }}
                aria-label={item.is_favorited === 1 ? "取消点赞" : "点赞"}
                title={item.is_favorited === 1 ? "已点赞，点击取消" : "点赞表示内容有用"}
              >
                <ThumbUpIcon filled={item.is_favorited === 1} />
              </button>
              <button
                type="button"
                className="ghost"
                onClick={() => onSelectItem(item)}
                aria-label={`查看 ${item.title} 详情`}
              >
                查看详情
              </button>
              {deletingId === item.id ? (
                <>
                  <button type="button" className="ghost" onClick={() => setDeletingId(null)}>
                    取消
                  </button>
                  <button
                    type="button"
                    className="danger"
                    onClick={() => {
                      onDeleteItem(item.id);
                      setDeletingId(null);
                    }}
                  >
                    确认删除
                  </button>
                </>
              ) : (
                <button type="button" className="danger" onClick={() => setDeletingId(item.id)}>
                  删除
                </button>
              )}
            </div>
          </article>
        ))}
        {knowledge.length === 0 && <p className="empty">没有匹配内容</p>}
      </div>
    </section>
  );
}
