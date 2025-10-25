import os
import requests
from typing import List, Dict, Optional


class OpenAIClient:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.base_url = (base_url or os.getenv("OPENAI_BASE_URL") or "https://api.openai.com").rstrip("/")
        self.org_id = os.getenv("OPENAI_ORG_ID") or os.getenv("OPENAI_ORGANIZATION")
        self.project = os.getenv("OPENAI_PROJECT")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not set")

    def chat(self, model: str, messages: List[Dict[str, str]], max_tokens: int = 1500, temperature: float = 0.7) -> str:
        url = f"{self.base_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if self.org_id:
            headers["OpenAI-Organization"] = self.org_id
        if self.project:
            headers["OpenAI-Project"] = self.project
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        try:
            # (connect timeout, read timeout)
            resp = requests.post(url, headers=headers, json=payload, timeout=(15, 120))
            resp.raise_for_status()
        except requests.exceptions.Timeout as e:
            raise RuntimeError(
                "OpenAI 요청 시간 초과: 네트워크/방화벽/프록시 설정을 확인하세요 (timeout 15s connect / 120s read)."
            ) from e
        except requests.exceptions.ConnectionError as e:
            raise RuntimeError(
                f"OpenAI 서버에 연결 실패: base_url={self.base_url}. 인터넷 연결과 프록시(HTTPS_PROXY) 설정을 확인하세요."
            ) from e
        except requests.exceptions.HTTPError as e:
            text = resp.text[:500] if 'resp' in locals() and resp is not None else ''
            raise RuntimeError(f"OpenAI API 오류 {resp.status_code if 'resp' in locals() else ''}: {text}") from e
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()

    def ping(self) -> str:
        """Quick connectivity/auth check. Returns short diagnostic string or raises RuntimeError."""
        url = f"{self.base_url}/v1/models"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }
        if self.org_id:
            headers["OpenAI-Organization"] = self.org_id
        if self.project:
            headers["OpenAI-Project"] = self.project
        try:
            resp = requests.get(url, headers=headers, timeout=(10, 20))
            if resp.status_code == 200:
                return "OK: reachable"
            return f"HTTP {resp.status_code}: {resp.text[:200]}"
        except requests.exceptions.Timeout as e:
            raise RuntimeError("OpenAI 연결/응답 시간 초과 (10/20s)") from e
        except requests.exceptions.ConnectionError as e:
            raise RuntimeError(f"OpenAI 연결 실패: base_url={self.base_url}") from e

    def quick_chat_test(self) -> str:
        """Minimal chat completion POST to verify POST path and auth.
        Uses tight timeouts to fail fast.
        """
        url = f"{self.base_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if self.org_id:
            headers["OpenAI-Organization"] = self.org_id
        if self.project:
            headers["OpenAI-Project"] = self.project
        payload = {
            "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Reply with: OK"},
            ],
            "max_tokens": 10,
            "temperature": 0,
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=(10, 30))
            resp.raise_for_status()
            data = resp.json()
            txt = data["choices"][0]["message"]["content"].strip()
            return f"OK chat: {txt[:50]}"
        except requests.exceptions.Timeout as e:
            raise RuntimeError("OpenAI chat POST 시간 초과 (10/30s)") from e
        except requests.exceptions.ConnectionError as e:
            raise RuntimeError("OpenAI chat POST 연결 실패") from e
        except requests.exceptions.HTTPError as e:
            return f"HTTP {resp.status_code}: {resp.text[:200]}"
