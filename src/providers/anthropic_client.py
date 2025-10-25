import os
import requests
from typing import List, Dict, Optional


class AnthropicClient:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, api_version: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self.base_url = (base_url or os.getenv("ANTHROPIC_BASE_URL") or "https://api.anthropic.com").rstrip("/")
        self.api_version = api_version or os.getenv("ANTHROPIC_API_VERSION", "2023-06-01")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is not set")

    def chat(self, model: str, messages: List[Dict[str, str]], max_tokens: int = 1500, temperature: float = 0.7) -> str:
        # Convert OpenAI-style messages into Anthropic role/content format
        system_texts = [m["content"] for m in messages if m["role"] == "system"]
        system = "\n\n".join(system_texts) if system_texts else None
        conv = []
        for m in messages:
            if m["role"] in ("user", "assistant"):
                conv.append({"role": m["role"], "content": m["content"]})

        url = f"{self.base_url}/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.api_version,
            "content-type": "application/json",
        }
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": conv,
        }
        if system:
            payload["system"] = system
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=(15, 300))
            resp.raise_for_status()
        except requests.exceptions.Timeout as e:
            raise RuntimeError(
                "Anthropic 요청 시간 초과: 네트워크/방화벽/프록시 설정을 확인하세요 (timeout 15s connect / 300s read)."
            ) from e
        except requests.exceptions.ConnectionError as e:
            raise RuntimeError(
                f"Anthropic 서버에 연결 실패: base_url={self.base_url}. 인터넷 연결과 프록시(HTTPS_PROXY) 설정을 확인하세요."
            ) from e
        except requests.exceptions.HTTPError as e:
            text = resp.text[:500] if 'resp' in locals() and resp is not None else ''
            status_code = resp.status_code if 'resp' in locals() else ''

            # Improved error message for 404 model not found
            if status_code == 404 and 'not_found_error' in text:
                raise RuntimeError(
                    f"Anthropic API 오류 404: 모델을 찾을 수 없습니다.\n"
                    f"사용 중인 모델: {model}\n"
                    f"최신 모델명으로 변경하세요:\n"
                    f"  - claude-sonnet-4-5 (최신 Claude 4.5, 자동 업데이트)\n"
                    f"  - claude-haiku-4-5 (빠르고 저렴)\n"
                    f"  - claude-3-7-sonnet-latest (Claude 3.7)\n"
                    f"  - claude-3-5-sonnet-20241022 (이전 3.5 버전)\n"
                    f".env 파일에서 ANTHROPIC_MODEL 환경변수를 설정하세요.\n"
                    f"원본 오류: {text}"
                ) from e

            raise RuntimeError(f"Anthropic API 오류 {status_code}: {text}") from e
        data = resp.json()
        # Concatenate content blocks
        parts = data.get("content", [])
        texts = []
        for p in parts:
            if p.get("type") == "text":
                texts.append(p.get("text", ""))
        return "".join(texts).strip()

    def ping(self) -> str:
        """Quick connectivity/auth check. Returns short diagnostic string or raises RuntimeError."""
        url = f"{self.base_url}/v1/models"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.api_version,
        }
        try:
            resp = requests.get(url, headers=headers, timeout=(10, 20))
            if resp.status_code == 200:
                return "OK: reachable"
            return f"HTTP {resp.status_code}: {resp.text[:200]}"
        except requests.exceptions.Timeout as e:
            raise RuntimeError("Anthropic 연결/응답 시간 초과 (10/20s)") from e
        except requests.exceptions.ConnectionError as e:
            raise RuntimeError(f"Anthropic 연결 실패: base_url={self.base_url}") from e

    def quick_chat_test(self) -> str:
        """Minimal chat POST to verify POST path and auth on Anthropic."""
        url = f"{self.base_url}/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.api_version,
            "content-type": "application/json",
        }
        model_name = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
        payload = {
            "model": model_name,
            "max_tokens": 10,
            "temperature": 0,
            "messages": [
                {"role": "user", "content": "Reply with: OK"}
            ],
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=(10, 30))
            resp.raise_for_status()
            data = resp.json()
            parts = data.get("content", [])
            text = "".join([p.get("text", "") for p in parts if p.get("type") == "text"]).strip()
            return f"OK chat: {text[:50]}"
        except requests.exceptions.Timeout as e:
            raise RuntimeError("Anthropic chat POST 시간 초과 (10/30s)") from e
        except requests.exceptions.ConnectionError as e:
            raise RuntimeError("Anthropic chat POST 연결 실패") from e
        except requests.exceptions.HTTPError as e:
            text = resp.text[:500] if 'resp' in locals() and resp is not None else ''
            status_code = resp.status_code if 'resp' in locals() else ''

            # Improved error message for 404 model not found
            if status_code == 404 and 'not_found_error' in text:
                return (
                    f"HTTP 404: 모델을 찾을 수 없습니다.\n"
                    f"사용 중인 모델: {model_name}\n"
                    f"최신 모델명으로 변경하세요:\n"
                    f"  - claude-sonnet-4-5 (최신 Claude 4.5, 자동 업데이트)\n"
                    f"  - claude-haiku-4-5 (빠르고 저렴)\n"
                    f"  - claude-3-7-sonnet-latest (Claude 3.7)\n"
                    f".env 파일에서 ANTHROPIC_MODEL을 설정하세요.\n"
                    f"원본 오류: {text[:200]}"
                )

            return f"HTTP {status_code}: {text[:200]}"
