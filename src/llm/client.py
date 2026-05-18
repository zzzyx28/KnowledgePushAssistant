

"""OpenAI 兼容客户端封装。"""

from openai import OpenAI


def create_client(base_url: str, api_key: str) -> OpenAI:
    if not api_key:
        api_key = "sk-placeholder"
    return OpenAI(base_url=base_url, api_key=api_key, timeout=60.0)


def assistant_message_to_dict(msg) -> dict:
    """将 assistant 回复转为可回传给 API 的消息 dict。

    thinking 模式下若本轮有 tool_calls，必须把 reasoning_content 一并带回，
    否则会返回 400 invalid_request_error。
    """
    entry: dict = {"role": "assistant"}
    if msg.content is not None:
        entry["content"] = msg.content
    reasoning = getattr(msg, "reasoning_content", None)
    if msg.tool_calls:
        # tool call 轮次必须带回 reasoning_content（可为空字符串）
        entry["reasoning_content"] = reasoning if reasoning is not None else ""
        entry["tool_calls"] = [
            {
                "id": tc.id,
                "type": getattr(tc, "type", None) or "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in msg.tool_calls
        ]
    elif reasoning is not None:
        entry["reasoning_content"] = reasoning
    return entry


def chat_completion(client: OpenAI, model: str, messages: list[dict],
                    tools: list[dict] = None, max_tokens: int = 4096):
    kwargs = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
    }
    if tools:
        kwargs["tools"] = tools
    return client.chat.completions.create(**kwargs)
