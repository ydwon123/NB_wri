#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""GUI 없이 직접 run 함수를 로그 콜백과 함께 테스트"""

import os
from dotenv import load_dotenv

load_dotenv()

# main.py의 run 함수 import
from src.main import run

# 간단한 로그 콜백
logs = []
def log_callback(msg):
    print(f"[LOG] {msg}")
    logs.append(msg)

print("=" * 60)
print("GUI 로그 콜백 테스트")
print("=" * 60)

# 테스트 파일 생성
test_file = "test_input.txt"
with open(test_file, "w", encoding="utf-8") as f:
    f.write("신발원 포장 테스트 내용입니다.")

print(f"\n테스트 파일 생성: {test_file}")
print("run() 함수 호출 시작...\n")

try:
    run(
        provider="anthropic",
        model=None,  # 기본값 사용
        purpose='"신발원 포장" 키워드로 블로그 맛집 1000자 작성해줘',
        input_dir=None,
        files=[test_file],
        out_path="test_output.txt",
        language="ko",
        max_tokens=1600,
        temperature=0.7,
        debug=False,
        log_callback=log_callback,
    )

    print("\n" + "=" * 60)
    print("성공! 로그 메시지 목록:")
    print("=" * 60)
    for i, log in enumerate(logs, 1):
        print(f"{i}. {log}")

    print(f"\n생성된 파일 확인:")
    if os.path.exists("test_output.txt"):
        with open("test_output.txt", "r", encoding="utf-8") as f:
            content = f.read()
            print(f"길이: {len(content)} 글자")
            print(f"처음 200자: {content[:200]}")
    else:
        print("파일이 생성되지 않았습니다!")

except Exception as e:
    print(f"\n오류 발생: {type(e).__name__}")
    print(f"메시지: {e}")
    import traceback
    print(f"\n상세:\n{traceback.format_exc()}")

    print("\n수집된 로그:")
    for i, log in enumerate(logs, 1):
        print(f"{i}. {log}")

# 정리
if os.path.exists(test_file):
    os.remove(test_file)
