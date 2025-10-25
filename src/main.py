import argparse
import os
from typing import List
from dotenv import load_dotenv

# Support both `python -m src.main` and `python src/main.py`
try:
    from .util.file_loader import load_attachments, chunk_text
    from .util.env_util import load_env
    from .prompt_templates import build_meta_prompt, build_final_prompt, format_attachments
    from .providers.openai_client import OpenAIClient
    from .providers.anthropic_client import AnthropicClient
except ImportError:  # running as a script without package context
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.util.file_loader import load_attachments, chunk_text
    from src.util.env_util import load_env
    from src.prompt_templates import build_meta_prompt, build_final_prompt, format_attachments
    from src.providers.openai_client import OpenAIClient
    from src.providers.anthropic_client import AnthropicClient


def run(provider: str, model: str, keyword: str, keyword_repeat: int, input_dir: str | None, files: List[str], out_path: str, language: str, max_tokens: int, temperature: float, debug: bool = False, log_callback=None, writing_guide: str | None = None):
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

    # Format attachments for prompts
    attachments_block = format_attachments(limited_attachments)

    log(f"[디버그] 메시지 구성 완료, 첨부 파일 {len(limited_attachments)}개")
    log(f"[디버그] Provider={provider}, Model={model or '(기본값 사용)'}")

    # Initialize client
    if provider == "openai":
        log("[디버그] OpenAI 클라이언트 초기화")
        client = OpenAIClient()
        # Set default model if not provided
        if not model:
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            log(f"[디버그] 기본 모델 사용: {model}")
    elif provider == "anthropic":
        log("[디버그] Anthropic 클라이언트 초기화")
        client = AnthropicClient()
        # Set default model if not provided
        if not model:
            model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
            log(f"[디버그] 기본 모델 사용: {model}")
    else:
        raise SystemExit("provider는 'openai' 또는 'anthropic'만 지원합니다.")

    # Step 1: Generate style prompt from attachments (meta-prompt)
    log("생성 중... (Step 1/2: 문체 분석)")
    meta_messages = build_meta_prompt(attachments_block)
    style_prompt = client.chat(model=model, messages=meta_messages, max_tokens=max_tokens, temperature=temperature)

    # Save Step 1 result (for debugging)
    base, ext = os.path.splitext(out_path)
    step1_path = f"{base}_step1_style_prompt{ext}"
    os.makedirs(os.path.dirname(os.path.abspath(step1_path)) or ".", exist_ok=True)
    with open(step1_path, "w", encoding="utf-8") as f:
        f.write(style_prompt)
    log(f"Step 1 결과 저장: {step1_path}")

    # Step 2: Generate final blog using style prompt
    log("생성 중... (Step 2/2: 블로그 작성)")
    final_messages = build_final_prompt(style_prompt, keyword, keyword_repeat, attachments_block, writing_guide)
    blog_draft = client.chat(model=model, messages=final_messages, max_tokens=max_tokens, temperature=temperature)

    # Save Step 2 result (final output)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(blog_draft)

    log(f"완료: {out_path}")


def main():
    parser = argparse.ArgumentParser(description="첨부자료 기반 블로그 초안 생성기 (OpenAI/Claude)")
    parser.add_argument("--provider", choices=["openai", "anthropic"], required=True, help="사용할 모델 제공자")
    parser.add_argument("--model", required=False, default=None, help="모델 이름 (미지정 시 기본값)")
    parser.add_argument("--keyword", "-k", required=True, help="키워드")
    parser.add_argument("--keyword-repeat", type=int, default=5, help="키워드 반복 횟수 (기본값: 5)")
    parser.add_argument("--input-dir", "-d", default=None, help="첨부자료 디렉토리 (재귀)" )
    parser.add_argument("files", nargs="*", help="개별 파일 경로 또는 glob 패턴 (다중)")
    parser.add_argument("--out", "-o", default="blog_draft.txt", help="출력 파일 경로")
    parser.add_argument("--lang", default="ko", help="ko 또는 en 등 출력 언어")
    parser.add_argument("--max-tokens", type=int, default=1600)
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--debug", action="store_true", help="환경/설정 진단 정보 출력")
    parser.add_argument("--writing-guide", "-g", required=True, help="주제 및 글쓰기 가이드 (톤앤매너, 필수 내용, 해시태그 등)")

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
        keyword=args.keyword,
        keyword_repeat=args.keyword_repeat,
        input_dir=args.input_dir,
        files=args.files,
        out_path=args.out,
        language=args.lang,
        max_tokens=args.max_tokens,
        temperature=args.temperature,
        debug=args.debug,
        writing_guide=args.writing_guide,
    )


if __name__ == "__main__":
    main()
