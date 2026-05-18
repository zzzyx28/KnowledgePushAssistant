"""ReAct 循环生成器 —— Agent 的核心执行引擎。

用 while 循环 + OpenAI 兼容 SDK 的 tool calling 实现，
每一步通过 yield 推送给 UI，实现 Agent 执行过程全透明。
"""

import json
import uuid
from typing import Generator

from openai import OpenAI
from sqlalchemy.orm import Session

from .tools import TOOL_SCHEMAS, ToolContext, execute_tool
from ..llm.client import assistant_message_to_dict
from ..storage import repository as repo


def react_loop(
    client: OpenAI,
    model: str,
    system_prompt: str,
    db_session: Session,
    on_push=None,
    max_turns: int = 6,
) -> Generator[dict, None, None]:
    """执行 ReAct 循环，通过 yield 返回每一步的状态。

    Yields:
        dict with keys:
            type: "thought" | "action" | "observation" | "final" | "error"
            tool_name: str (仅 action/observation)
            args: dict (仅 action)
            result: str (仅 observation)
            content: str (thought/final/error)
    """
    session_id = str(uuid.uuid4())
    ctx = ToolContext(session=db_session, on_push=on_push, restrict_web_tools=True)

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": (
                "请判断当前是否适合推送知识卡片。"
                "先用工具了解用户设置、历史、反馈和领域信息，"
                "选定领域与知识点后，由你直接撰写并调用 pushKnowledgeCard；"
                "不要依赖网页搜索，也不要因搜索无结果而 skipPush。"
                "仅当推送时机或设置明显不合适时才 skipPush。"
            ),
        },
    ]

    for step in range(max_turns):
        # 每轮开始前刷新 session，确保读到最新的领域/设置变更
        db_session.expire_all()

        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=TOOL_SCHEMAS,
                max_tokens=4096,
                timeout=60.0,
            )
        except Exception as e:
            repo.save_agent_log(db_session, session_id, "error", content=str(e))
            yield {"type": "error", "content": f"LLM 调用失败: {str(e)}"}
            return

        msg = response.choices[0].message

        if msg.content:
            repo.save_agent_log(
                db_session, session_id, "thought", content=msg.content
            )
            yield {"type": "thought", "content": msg.content}

        if msg.tool_calls:
            messages.append(assistant_message_to_dict(msg))

            for tc in msg.tool_calls:
                tool_name = tc.function.name
                try:
                    args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    args = {}

                repo.save_agent_log(
                    db_session, session_id, "action",
                    tool_name=tool_name,
                    tool_input=tc.function.arguments,
                )
                yield {
                    "type": "action",
                    "tool_name": tool_name,
                    "args": args,
                }

                result = execute_tool(ctx, tool_name, args)

                repo.save_agent_log(
                    db_session, session_id, "observation",
                    tool_name=tool_name,
                    tool_output=result,
                )
                yield {
                    "type": "observation",
                    "tool_name": tool_name,
                    "result": result,
                }

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })

                # 工具执行后立即提交，确保写入持久化
                try:
                    db_session.commit()
                except Exception:
                    db_session.rollback()

                if tool_name in ("pushKnowledgeCard", "skipPush"):
                    repo.save_agent_log(
                        db_session, session_id, "final",
                        content=f"决策: {tool_name}",
                    )
                    yield {
                        "type": "final",
                        "content": f"决策完成: {tool_name}",
                        "result": result,
                    }
                    return
        else:
            repo.save_agent_log(
                db_session, session_id, "final", content=msg.content or ""
            )
            yield {
                "type": "final",
                "content": msg.content or "Agent 未做出明确决策",
            }
            return

    repo.save_agent_log(db_session, session_id, "error", content="达到最大轮次")
    yield {"type": "error", "content": "达到最大执行轮次，Agent 未做出决策"}
