#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""GUI 강제 재로드 실행 스크립트"""

import sys
import importlib

# 기존 src 모듈 모두 제거 (강제 재로드)
modules_to_remove = [key for key in sys.modules.keys() if key.startswith('src')]
for module in modules_to_remove:
    del sys.modules[module]

# 새로 import
from src.gui import main

if __name__ == "__main__":
    main()
