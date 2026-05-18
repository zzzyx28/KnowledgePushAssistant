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
from ..storage import repository as repo


def react_loop(
    client: OpenAI,
    model: str,
    system_prompt: str,
    db_session: Session,
    on_push=None,
    max_turns: int = 10,
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
    ctx = ToolContext(session=db_session, on_push=on_push)

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": (
                "请判断当前是否适合推送知识卡片。"
                "先通过工具了解用户设置、历史、反馈和领域信息，"
                "然后搜索素材并决定推送或跳过。"
            ),
        },
    ]

    for step in range(max_turns):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=TOOL_SCHEMAS,
                max_tokens=4096,
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
                    "role": "assistant",
                    "content": msg.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                    ],
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })

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
