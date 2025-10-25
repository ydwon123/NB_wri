"""
2-pass workflow 테스트 스크립트
Step 1: 문체 분석 프롬프트 생성
Step 2: 최종 블로그 작성
"""
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from prompt_templates import build_meta_prompt, build_final_prompt, format_attachments

def test_prompts():
    print("=" * 60)
    print("2-Pass 워크플로우 프롬프트 테스트")
    print("=" * 60)

    # 샘플 첨부자료
    sample_attachments = [
        ("sample_blog.txt", """
안녕하세요! 오늘은 맛집 탐방기를 준비했어요.
신발원은 정말 유명한 곳이죠. 포장도 가능하답니다.
직접 방문해서 먹어본 후기를 공유할게요.

맛은 정말 환상적이었어요. 특히 양념이 일품이었습니다.
가격도 합리적이고, 직원분들도 친절하셨어요.
다음에 또 방문하고 싶은 곳이에요.
        """)
    ]

    # Format attachments
    attachments_block = format_attachments(sample_attachments)
    print("\n[첨부자료 포맷팅 완료]")
    print(attachments_block[:200])
    print("...\n")

    # Step 1: Meta prompt
    print("\n" + "=" * 60)
    print("Step 1: 메타프롬프트 생성")
    print("=" * 60)
    meta_messages = build_meta_prompt(attachments_block)
    print(f"Role: {meta_messages[0]['role']}")
    print(f"Content:\n{meta_messages[0]['content'][:300]}...")

    # Simulate Step 1 response
    simulated_style_prompt = """
- 친근하고 경험적인 어투 사용 (예: "~해요", "~랍니다")
- 실제 방문 경험을 바탕으로 한 후기 형식
- 감정 표현 적극 활용 (예: "정말 환상적", "일품")
- 짧은 문단으로 구성하여 가독성 확보
- 구체적인 특징 언급 (맛, 가격, 서비스)
    """

    print(f"\n[시뮬레이션] Step 1 응답:\n{simulated_style_prompt}")

    # Step 2: Final prompt
    print("\n" + "=" * 60)
    print("Step 2: 최종 블로그 생성 프롬프트")
    print("=" * 60)

    # 주제 및 가이드 시뮬레이션
    simulated_writing_guide = """
주제: 블로그 맛집 리뷰

📄내용 가이드라인
- 신규로 오픈한 고깃집의 매력을 소개
- 관광지 주변에 위치하여 교통이 편리하고 주차장이 있음을 강조
- 직원의 친절함과 단체석이 있어 가족 단위 방문에 적합한 점을 언급

해시태그:
#고기맛집, #금오산맛집, #원평동맛집
    """

    final_messages = build_final_prompt(
        style_prompt=simulated_style_prompt,
        keyword="신발원 포장",
        keyword_repeat=5,
        attachments_block=attachments_block,
        writing_guide=simulated_writing_guide
    )
    print(f"Role: {final_messages[0]['role']}")
    print(f"Content:\n{final_messages[0]['content'][:500]}...")

    print("\n" + "=" * 60)
    print("✅ 프롬프트 생성 테스트 완료!")
    print("=" * 60)

if __name__ == "__main__":
    test_prompts()
