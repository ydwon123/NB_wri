from typing import List, Tuple


def build_system_prompt(language: str = "ko") -> str:
    if language.lower().startswith("ko"):
        return (
            "너는 전문 블로그 에디터이자 SEO 컨설턴트야. "
            "독자가 쉽게 이해하도록 구조화하고, 검색 친화적인 제목과 소제목을 사용해. "
            "근거는 첨부자료에서만 가져오고, 추측은 최소화해. 필요하면 명확히 가정이라고 표시해."
        )
    return (
        "You are a professional blog editor and SEO consultant. "
        "Structure content for clarity, use search-friendly headings, and ground claims in attachments."
    )


def format_attachments(attachments: List[Tuple[str, str]], max_chars_per_doc: int = 12000) -> str:
    blocks = []
    for idx, (path, content) in enumerate(attachments, start=1):
        snippet = content if len(content) <= max_chars_per_doc else content[:max_chars_per_doc] + "\n...[truncated]"
        blocks.append(f"[자료 {idx}] {path}\n```\n{snippet}\n```")
    return "\n\n".join(blocks)


def build_user_prompt(purpose: str, attachments_block: str, language: str = "ko") -> str:
    if language.lower().startswith("ko"):
        return f"""
아래 [첨부자료]를 바탕으로, 다음 [목적]에 정확히 부합하는 블로그 초안을 작성해줘.

[목적]
- {purpose}

[요구사항]
- 글머리: 한 줄 요약과 훅(hook)
- 구조: H2/H3 소제목으로 명확히 구분, 불릿/번호 목록 적극 활용
- 톤앤매너: 전문가적이지만 친근하고 실용적으로
- 범위: 첨부자료 기반으로 충실히, 근거 없는 확장은 금지
- 인용: 필요한 곳에 출처(파일명/섹션) 표기
- SEO: 메타 설명(150자 내외), 핵심 키워드 5~10개, 슬러그 제안
- 산출물: Markdown (.md) 포맷, 코드/표는 Markdown 규칙 준수

[출력 템플릿]
# 제목

> 요약 한 줄 (120자 내외)

## 개요
- 대상 독자·문제 정의·핵심 메시지

## 본문 섹션 1
내용…

## 본문 섹션 2
내용…

## 결론
- 핵심 요점 3~5개 불릿
- 다음 행동 제안(CTA)

---
SEO 메타 설명: ...
핵심 키워드: ...
추천 슬러그: ...

[첨부자료]
{attachments_block}
""".strip()
    else:
        return f"""
Using the [Attachments] below, write a blog draft tailored to the following [Purpose].

[Purpose]
- {purpose}

[Requirements]
- Hooked opening line; clear H2/H3 structure
- Professional yet friendly tone; practical and concise
- Stay grounded in attachments; mark assumptions explicitly
- SEO section: meta description, 5–10 keywords, slug suggestion
- Output Markdown (.md)

[Output Template]
# Title

> One-line summary

## Overview
- Audience, problem, key message

## Section 1
...

## Section 2
...

## Conclusion
- 3–5 key bullets
- CTA

---
SEO Meta: ...
Keywords: ...
Slug: ...

[Attachments]
{attachments_block}
""".strip()

