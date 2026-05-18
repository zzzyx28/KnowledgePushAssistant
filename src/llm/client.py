

"""OpenAI 兼容客户端封装。"""

from openai import OpenAI


def create_client(base_url: str, api_key: str) -> OpenAI:
    if not api_key:
        api_key = "sk-placeholder"
    return OpenAI(base_url=base_url, api_key=api_key)


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
