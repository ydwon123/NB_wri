import argparse
import os
from typing import List
from dotenv import load_dotenv

# Support both `python -m src.main` and `python src/main.py`
try:
    from .util.file_loader import load_attachments, chunk_text
    from .util.env_util import load_env
    from .prompt_templates import build_system_prompt, build_user_prompt, format_attachments
    from .providers.openai_client import OpenAIClient
    from .providers.anthropic_client import AnthropicClient
except ImportError:  # running as a script without package context
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.util.file_loader import load_attachments, chunk_text
    from src.util.env_util import load_env
    from src.prompt_templates import build_system_prompt, build_user_prompt, format_attachments
    from src.providers.openai_client import OpenAIClient
    from src.providers.anthropic_client import AnthropicClient


def build_messages(purpose: str, attachments: list[tuple[str, str]], language: str) -> list[dict[str, str]]:
    system = build_system_prompt(language)
    attachments_block = format_attachments(attachments)
    user = build_user_prompt(purpose, attachments_block, language)
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def run(provider: str, model: str, purpose: str, input_dir: str | None, files: List[str], out_path: str, language: str, max_tokens: int, temperature: float, debug: bool = False, log_callback=None):
    def log(msg):
        """로그 출력 - log_callback이 있으면 사용, 없으면 print"""
        if log_callback:
            log_callback(msg)
        else:
            print(msg)

    env_info = load_env(verbose=debug)
    if debug:
        log("[debug] Provider=" + provider)
        log("[debug] Model=" + (model or "(default)"))
        log("[debug] Lang=" + language)

    # Load attachments (optional - can be empty)
    if files:
        log(f"[디버그] 파일 로딩 시작: {len(files)}개 파일 처리")
        attachments = load_attachments(input_dir, files)
        log(f"[디버그] 파일 로딩 완료: {len(attachments)}개 첨부 파일")
    else:
        log("[디버그] 첨부 파일 없음 - 프롬프트만으로 생성")
        attachments = []

    # Concatenate large files naïvely (chunking per file kept for future multi-turn)
    limited_attachments: list[tuple[str, str]] = []
    for path, content in attachments:
        chunks = chunk_text(content, max_chars=12000)
        # take only first chunk to avoid token overflow in a single call
        limited_attachments.append((path, chunks[0]))

    messages = build_messages(purpose, limited_attachments, language)

    log(f"[디버그] 메시지 구성 완료, 첨부 파일 {len(limited_attachments)}개")
    log(f"[디버그] Provider={provider}, Model={model or '(기본값 사용)'}")

    if provider == "openai":
        log("[디버그] OpenAI 클라이언트 초기화")
        client = OpenAIClient()
        # Set default model if not provided
        if not model:
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            log(f"[디버그] 기본 모델 사용: {model}")
        log("[디버그] OpenAI API 호출 중...")
        output = client.chat(model=model, messages=messages, max_tokens=max_tokens, temperature=temperature)
    elif provider == "anthropic":
        log("[디버그] Anthropic 클라이언트 초기화")
        client = AnthropicClient()
        # Set default model if not provided
        if not model:
            model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
            log(f"[디버그] 기본 모델 사용: {model}")
        log(f"[디버그] Anthropic API 호출 중... (timeout: 15s connect, 300s read)")
        output = client.chat(model=model, messages=messages, max_tokens=max_tokens, temperature=temperature)
        log("[디버그] Anthropic API 응답 수신 완료")
    else:
        raise SystemExit("provider는 'openai' 또는 'anthropic'만 지원합니다.")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(output)

    log(f"완료: {out_path}")


def main():
    parser = argparse.ArgumentParser(description="첨부자료 기반 블로그 초안 생성기 (OpenAI/Claude)")
    parser.add_argument("--provider", choices=["openai", "anthropic"], required=True, help="사용할 모델 제공자")
    parser.add_argument("--model", required=False, default=None, help="모델 이름 (미지정 시 기본값)")
    parser.add_argument("--purpose", "-p", required=True, help="글쓰기 목적/타깃/톤 등 지시문")
    parser.add_argument("--input-dir", "-d", default=None, help="첨부자료 디렉토리 (재귀)" )
    parser.add_argument("files", nargs="*", help="개별 파일 경로 또는 glob 패턴 (다중)")
    parser.add_argument("--out", "-o", default="blog_draft.txt", help="출력 파일 경로")
    parser.add_argument("--lang", default="ko", help="ko 또는 en 등 출력 언어")
    parser.add_argument("--max-tokens", type=int, default=1600)
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--debug", action="store_true", help="환경/설정 진단 정보 출력")

    args = parser.parse_args()

    # sensible default models
    model = args.model
    if not model:
        if args.provider == "openai":
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        else:
            model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")

    run(
        provider=args.provider,
        model=model,
        purpose=args.purpose,
        input_dir=args.input_dir,
        files=args.files,
        out_path=args.out,
        language=args.lang,
        max_tokens=args.max_tokens,
        temperature=args.temperature,
        debug=args.debug,
    )


if __name__ == "__main__":
    main()
