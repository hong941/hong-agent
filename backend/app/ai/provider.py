import httpx

from ..config import get_settings


class LLMProvider:
    def complete(self, messages: list[dict], temperature: float = 0.2) -> str:
        raise NotImplementedError


class MockProvider(LLMProvider):
    """Deterministic local provider used when no LLM API key is configured."""

    def complete(self, messages: list[dict], temperature: float = 0.2) -> str:
        last = messages[-1]["content"] if messages else ""
        return (
            "已根据当前就诊信息完成评估。请以分诊台给出的风险等级和科室建议为准，"
            "如症状加重或出现新发高危症状，请立即前往急诊。"
        )


class OpenAICompatibleProvider(LLMProvider):
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        timeout: int,
        style: str = "auto",
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.style = style

    def _use_anthropic(self) -> bool:
        return self.style == "anthropic" or (
            self.style == "auto" and "anthropic" in self.base_url
        )

    def complete(self, messages: list[dict], temperature: float = 0.2) -> str:
        if self._use_anthropic():
            response = httpx.post(
                f"{self.base_url}/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "max_tokens": 1024,
                    "temperature": temperature,
                    "messages": messages,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            for block in data["content"]:
                if block.get("type") == "text":
                    return block.get("text", "").strip()
            return ""

        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()


def get_provider() -> LLMProvider:
    settings = get_settings()
    if settings.llm_api_key:
        return OpenAICompatibleProvider(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            model=settings.llm_model,
            timeout=settings.llm_timeout,
            style=settings.llm_style,
        )
    return MockProvider()
