from typing import List, Tuple


def format_attachments(attachments: List[Tuple[str, str]], max_chars_per_doc: int = 12000) -> str:
    """첨부자료를 마크다운 블록으로 포맷팅"""
    blocks = []
    for idx, (path, content) in enumerate(attachments, start=1):
        snippet = content if len(content) <= max_chars_per_doc else content[:max_chars_per_doc] + "\n...[truncated]"
        blocks.append(f"[자료 {idx}] {path}\n```\n{snippet}\n```")
    return "\n\n".join(blocks)


def build_meta_prompt(attachments_block: str) -> list[dict[str, str]]:
    """Step 1: 첨부문서의 문체를 분석하여 재현 가능한 스타일 가이드 생성"""
    system_prompt = """당신은 블로그 글의 문체를 정밀하게 분석하고, 동일한 스타일로 글을 작성할 수 있는 스타일 가이드를 생성하는 전문가입니다.

제공된 블로그 글들을 분석하여 다음 요소들을 파악하고, 구체적인 작성 가이드라인을 만들어주세요:

1. 문장 구조 및 리듬
   - 문장 길이 패턴 (단문/중문/장문 비율)
   - 문단 구성 방식
   - 줄바꿈 및 여백 활용
   - 이모티콘 사용 빈도 및 위치

2. 어조 및 톤
   - 존댓말/반말 사용 패턴
   - 친근감 표현 방식
   - 감정 표현 강도
   - 독자와의 거리감

3. 어휘 및 표현
   - 자주 사용하는 어미 (예: ~해요, ~더라고요, ~네요)
   - 특정 표현 패턴
   - 강조 표현 방식
   - 구어체 vs 문어체 비율

4. 콘텐츠 구성
   - 정보 전달 순서
   - 섹션 구분 방식
   - 사진/정보 설명 방식

5. 개성 있는 특징
   - 반복되는 표현 습관
   - 독특한 문체적 특징

다음 형식으로 스타일 가이드를 작성해주세요:

## 문체 핵심 특징
[3-5개 bullet points]

## 어조 및 톤
[구체적 설명]

## 문장 구조
[문장 길이, 문단 구성, 줄바꿈 규칙]

## 표현 스타일
- 자주 사용할 어미: [예시]
- 이모티콘 사용: [빈도 및 종류]
- 강조 표현: [방식]

## 콘텐츠 구조
[도입부, 본문, 마무리 작성법]

## 피해야 할 표현
[이 블로거가 사용하지 않는 표현들]"""

    return [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": f"다음 블로그 글들을 분석하여 이 블로거만의 스타일 가이드를 만들어주세요.\n\n{attachments_block}"
        }
    ]


def build_final_prompt(style_prompt: str, keyword: str, keyword_repeat: int, attachments_block: str, writing_guide: str | None = None) -> list[dict[str, str]]:
    """Step 2: 최종 블로그 생성 프롬프트"""

    # 글쓰기 가이드 섹션 (필수)
    guide_section = ""
    if writing_guide:
        guide_section = f"\n[주제 및 작성 가이드]\n{writing_guide}\n"

    user_content = f"""[작성 스타일]
{style_prompt}
{guide_section}
위 주제와 가이드에 맞춰 블로그 글을 작성해줘.
["{keyword}"]는 {keyword_repeat}회 반복해줘.
첨부문서 형태소를 분석해서 가장 많이 사용된 단어 10개를 선택해서 적절하게 사용해.

[첨부자료]
{attachments_block}
"""
    return [{"role": "user", "content": user_content}]
