#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""간단한 테스트 스크립트 - Anthropic API 호출 테스트"""

import os
import sys
from dotenv import load_dotenv
from src.providers.anthropic_client import AnthropicClient

# UTF-8 출력 설정
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# .env 로드
load_dotenv()

print("=" * 60)
print("Anthropic API 간단 테스트")
print("=" * 60)

# API 키 확인
api_key = os.getenv("ANTHROPIC_API_KEY", "")
if not api_key:
    print("[X] ANTHROPIC_API_KEY가 설정되지 않았습니다!")
    exit(1)

print(f"[OK] API 키 확인: {api_key[:20]}...{api_key[-10:]}")

# 클라이언트 생성
print("\n[1] Anthropic 클라이언트 초기화 중...")
try:
    client = AnthropicClient()
    print("[OK] 클라이언트 초기화 성공")
except Exception as e:
    print(f"[X] 클라이언트 초기화 실패: {e}")
    exit(1)

# 간단한 메시지로 테스트
print("\n[2] 간단한 API 호출 테스트...")
messages = [
    {"role": "user", "content": "Hello, reply with just 'OK'"}
]

try:
    print("   - 요청 전송 중...")
    response = client.chat(
        model="claude-sonnet-4-5",
        messages=messages,
        max_tokens=50,
        temperature=0.7
    )
    print(f"[OK] 응답 수신 성공!")
    print(f"   응답 내용: {response}")
except Exception as e:
    print(f"[X] API 호출 실패: {type(e).__name__}")
    print(f"   오류 메시지: {e}")
    import traceback
    print(f"\n상세 오류:\n{traceback.format_exc()}")
    exit(1)

# 블로그 글 생성 테스트
print("\n[3] 블로그 글 생성 테스트...")
messages = [
    {"role": "system", "content": "당신은 블로그 작가입니다."},
    {"role": "user", "content": '"신발원 포장" 키워드로 블로그 맛집 1000자 작성해줘'}
]

try:
    print("   - 요청 전송 중... (최대 300초 대기)")
    response = client.chat(
        model="claude-sonnet-4-5",
        messages=messages,
        max_tokens=1600,
        temperature=0.7
    )
    print(f"[OK] 블로그 글 생성 성공!")
    print(f"   응답 길이: {len(response)} 글자")
    print(f"\n--- 생성된 내용 (처음 200자) ---")
    print(response[:200])
    print("...")
except Exception as e:
    print(f"[X] 블로그 글 생성 실패: {type(e).__name__}")
    print(f"   오류 메시지: {e}")
    import traceback
    print(f"\n상세 오류:\n{traceback.format_exc()}")
    exit(1)

print("\n" + "=" * 60)
print("[OK] 모든 테스트 완료!")
print("=" * 60)
