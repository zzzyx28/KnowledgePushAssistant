import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { askKnowledgeQuestion, type AskMessage } from "../core/agent/ask";
import type { AppSettings, KnowledgeItem } from "../core/types";

const ASK_HEIGHT_KEY = "kpa-ask-panel-height";
const DEFAULT_ASK_HEIGHT = 300;
const MIN_ASK_HEIGHT = 160;

function readSavedAskHeight(): number {
  const saved = localStorage.getItem(ASK_HEIGHT_KEY);
  const parsed = saved ? Number(saved) : NaN;
  return Number.isFinite(parsed) && parsed >= MIN_ASK_HEIGHT ? parsed : DEFAULT_ASK_HEIGHT;
}

interface DetailOverlayProps {
  open: boolean;
  item: KnowledgeItem | null;
  settings: AppSettings;
  loading?: boolean;
  onClose: () => void;
  onExited: () => void;
}

export default function DetailOverlay({
  open,
  item,
  settings,
  loading = false,
  onClose,
  onExited
}: DetailOverlayProps) {
  const [askExpanded, setAskExpanded] = useState(false);
  const [messages, setMessages] = useState<AskMessage[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [askError, setAskError] = useState<string | null>(null);
  const [askHeight, setAskHeight] = useState(readSavedAskHeight);
  const bubblesRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const bodyRef = useRef<HTMLDivElement>(null);
  const askHeightRef = useRef(askHeight);
  const dragRef = useRef<{ startY: number; startH: number } | null>(null);
  askHeightRef.current = askHeight;

  useEffect(() => {
    setMessages([]);
    setInput("");
    setAskExpanded(false);
    setAskError(null);
    setBusy(false);
  }, [item?.id]);

  useEffect(() => {
    const node = bubblesRef.current;
    if (node) {
      node.scrollTop = node.scrollHeight;
    }
  }, [messages, busy, askExpanded]);

  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  useEffect(() => {
    const onMove = (event: MouseEvent) => {
      if (!dragRef.current || !bodyRef.current) return;
      const maxHeight = Math.max(MIN_ASK_HEIGHT, bodyRef.current.clientHeight - 100);
      const delta = dragRef.current.startY - event.clientY;
      const next = Math.min(maxHeight, Math.max(MIN_ASK_HEIGHT, dragRef.current.startH + delta));
      setAskHeight(next);
    };
    const onUp = () => {
      if (!dragRef.current) return;
      dragRef.current = null;
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
      localStorage.setItem(ASK_HEIGHT_KEY, String(askHeightRef.current));
    };
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
    return () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    };
  }, []);

  function startAskResize(event: React.MouseEvent<HTMLDivElement>) {
    event.preventDefault();
    dragRef.current = { startY: event.clientY, startH: askHeightRef.current };
    document.body.style.cursor = "ns-resize";
    document.body.style.userSelect = "none";
  }

  function handleOverlayTransitionEnd(event: React.TransitionEvent<HTMLElement>) {
    if (event.target !== event.currentTarget || event.propertyName !== "opacity") return;
    if (!open) onExited();
  }

  async function sendAsk() {
    const text = input.trim();
    if (!text || busy || !item) return;

    if (!askExpanded) setAskExpanded(true);

    const nextMessages: AskMessage[] = [...messages, { role: "user", content: text }];
    setMessages(nextMessages);
    setInput("");
    setAskError(null);
    setBusy(true);

    try {
      const reply = await askKnowledgeQuestion({
        settings,
        item,
        messages: nextMessages
      });
      setMessages((prev) => [...prev, { role: "assistant", content: reply }]);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      setAskError(message);
      setMessages((prev) => prev.slice(0, -1));
    } finally {
      setBusy(false);
      inputRef.current?.focus();
    }
  }

  if (!item && !open) return null;

  return (
    <section
      className={`detail-overlay${open ? " is-open" : ""}`}
      role="dialog"
      aria-modal="true"
      aria-label="知识详情"
      aria-hidden={!open}
      onClick={onClose}
      onTransitionEnd={handleOverlayTransitionEnd}
    >
      <article className="detail-sheet" onClick={(e) => e.stopPropagation()}>
        <header className="detail-header">
          <div>
            <p className="detail-bar-title">知识详情</p>
            <h3>{item?.title ?? "加载中…"}</h3>
          </div>
          <button type="button" className="primary" onClick={onClose}>
            完成
          </button>
        </header>

        <div ref={bodyRef} className={`detail-body${askExpanded ? " ask-expanded" : ""}`}>
          <div className="detail-scroll">
            {loading && <p className="detail-loading">正在加载详情…</p>}
            {item && !loading && (
              <>
                <p className="detail-meta">
                  <span className="detail-tag">{item.domain_name || "未分类"}</span>
                  <span>{new Date(item.created_at).toLocaleString()}</span>
                  {item.source_url && (
                    <a href={item.source_url} target="_blank" rel="noreferrer">
                      查看原文
                    </a>
                  )}
                </p>
                {item.summary && <p className="detail-summary">{item.summary}</p>}
                <div className="markdown-body">
                  {item.detail?.trim() ? (
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{item.detail}</ReactMarkdown>
                  ) : (
                    <p className="empty">暂无详细内容</p>
                  )}
                </div>
              </>
            )}
          </div>

          {askExpanded && (
            <div
              className="ask-resize-handle"
              role="separator"
              aria-orientation="horizontal"
              aria-label="调整问一问区域高度"
              onMouseDown={startAskResize}
            />
          )}

          <aside
            className={`detail-ask${askExpanded ? " is-expanded" : ""}`}
            style={askExpanded ? { height: askHeight } : undefined}
          >
            <div className="ask-header">
              <div className="ask-header-text">
                <strong>问一问</strong>
                <span>基于本条知识提问，AI 即时回答</span>
              </div>
              <button
                type="button"
                className="ghost ask-toggle"
                onClick={() => setAskExpanded((prev) => !prev)}
                aria-expanded={askExpanded}
                aria-label={askExpanded ? "收起问答" : "展开问答"}
              >
                {askExpanded ? "—" : "+"}
              </button>
            </div>

            {askExpanded && (
              <>
                <div className="ask-messages" ref={bubblesRef}>
                  {messages.length === 0 && !busy && !askError && (
                    <p className="ask-empty">在下方输入你的问题，AI 将基于本条知识内容进行回答</p>
                  )}
                  {messages.map((msg, index) => (
                    <div
                      key={`${msg.role}-${index}`}
                      className={`ask-bubble-row${msg.role === "user" ? " is-user" : ""}`}
                    >
                      <div className={`ask-bubble${msg.role === "user" ? " is-user" : " is-ai"}`}>
                        {msg.role === "assistant" ? (
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                        ) : (
                          <p>{msg.content}</p>
                        )}
                      </div>
                    </div>
                  ))}
                  {busy && (
                    <div className="ask-bubble-row">
                      <div className="ask-bubble is-ai is-pending">
                        <p>思考中…</p>
                      </div>
                    </div>
                  )}
                  {askError && (
                    <div className="ask-bubble-row">
                      <div className="ask-bubble is-error">
                        <p>{askError}</p>
                      </div>
                    </div>
                  )}
                </div>

                <form
                  className="ask-composer"
                  onSubmit={(e) => {
                    e.preventDefault();
                    void sendAsk();
                  }}
                >
                  <input
                    ref={inputRef}
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="基于本条知识提问…"
                    disabled={busy || loading || !item}
                    autoComplete="off"
                  />
                  <button className="primary" type="submit" disabled={busy || loading || !item}>
                    发送
                  </button>
                </form>
              </>
            )}
          </aside>
        </div>
      </article>
    </section>
  );
}
