import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Set

from dotenv import load_dotenv

# Support both `python -m src.gui` and double-click/`python src/gui.py`
try:
    from .main import run as cli_run
    from .util.env_util import load_env
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.main import run as cli_run
    from src.util.env_util import load_env


def walk_files(dirs: List[str]) -> List[str]:
    files: List[str] = []
    for d in dirs:
        for root, _, names in os.walk(d):
            for n in names:
                files.append(os.path.join(root, n))
    return files


class BlogDraftGUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("블로그 초안 생성기 (OpenAI / Claude)")
        self.geometry("860x640")
        self.minsize(820, 600)

        # Load .env from project root and CWD (diagnostic-aware)
        info = load_env(verbose=False)
        self.loaded_env_info = info

        self.selected_files: List[str] = []
        self._build_widgets()

    # UI
    def _build_widgets(self) -> None:
        # Input Fields: Keyword, Topic, Word Count
        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=10, pady=8)

        ttk.Label(top, text="키워드").grid(row=0, column=0, sticky=tk.W, padx=(0, 6))
        self.keyword = ttk.Entry(top, width=30)
        self.keyword.grid(row=0, column=1, sticky=tk.W)

        ttk.Label(top, text="주제").grid(row=0, column=2, sticky=tk.W, padx=(16, 6))
        self.topic = ttk.Entry(top, width=40)
        self.topic.grid(row=0, column=3, sticky=tk.W+tk.E)

        ttk.Label(top, text="글자수").grid(row=1, column=0, sticky=tk.W, pady=(8, 0))
        self.word_count = ttk.Entry(top, width=12)
        self.word_count.insert(0, "1000")
        self.word_count.grid(row=1, column=1, sticky=tk.W, pady=(8, 0))

        top.columnconfigure(3, weight=1)

        # Attachments (Optional)
        attach_fr = ttk.LabelFrame(self, text="첨부자료 (선택사항 - 참고 문서가 있을 경우)")
        attach_fr.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

        btns = ttk.Frame(attach_fr)
        btns.pack(fill=tk.X, padx=6, pady=(6, 2))
        ttk.Button(btns, text="파일 추가", command=self.add_files).pack(side=tk.LEFT)
        ttk.Button(btns, text="폴더 추가", command=self.add_folder).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(btns, text="선택 제거", command=self.remove_selected).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(btns, text="전체 비우기", command=self.clear_all).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(btns, text="환경 점검", command=self.check_env).pack(side=tk.LEFT, padx=(12, 0))
        ttk.Button(btns, text="연결 테스트", command=self.ping_provider).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(btns, text="짧은 생성 테스트", command=self.quick_chat_test).pack(side=tk.LEFT, padx=(6, 0))

        self.listbox = tk.Listbox(attach_fr, selectmode=tk.EXTENDED)
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))

        # Output Path
        out_fr = ttk.Frame(self)
        out_fr.pack(fill=tk.X, padx=10, pady=6)
        ttk.Label(out_fr, text="출력 파일").pack(side=tk.LEFT)
        self.out_path = ttk.Entry(out_fr)
        self.out_path.insert(0, "blog_draft.txt")
        self.out_path.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 6))
        ttk.Button(out_fr, text="찾아보기", command=self.choose_output).pack(side=tk.LEFT)

        # Run
        run_fr = ttk.Frame(self)
        run_fr.pack(fill=tk.X, padx=10, pady=(2, 6))
        self.status_var = tk.StringVar(value="API 키는 환경변수 또는 .env에 설정하세요.")
        ttk.Label(run_fr, textvariable=self.status_var).pack(side=tk.LEFT)
        ttk.Button(run_fr, text="생성 시작", command=self.start_generation).pack(side=tk.RIGHT)

        # Log
        log_fr = ttk.LabelFrame(self, text="로그")
        log_fr.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.log = tk.Text(log_fr, height=10)
        self.log.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

    # Actions
    def add_files(self) -> None:
        paths = filedialog.askopenfilenames(title="첨부할 파일 선택")
        if not paths:
            return
        self._add_unique(paths)

    def add_folder(self) -> None:
        d = filedialog.askdirectory(title="첨부할 폴더 선택")
        if not d:
            return
        files = walk_files([d])
        self._add_unique(files)

    def remove_selected(self) -> None:
        sel = list(self.listbox.curselection())
        sel.sort(reverse=True)
        for idx in sel:
            path = self.listbox.get(idx)
            try:
                self.selected_files.remove(path)
            except ValueError:
                pass
            self.listbox.delete(idx)

    def clear_all(self) -> None:
        self.selected_files.clear()
        self.listbox.delete(0, tk.END)

    def choose_output(self) -> None:
        initial = self.out_path.get() or "blog_draft.txt"
        path = filedialog.asksaveasfilename(title="출력 파일 경로", defaultextension=".txt", initialfile=os.path.basename(initial))
        if path:
            self.out_path.delete(0, tk.END)
            self.out_path.insert(0, path)

    def _add_unique(self, paths: List[str]) -> None:
        seen: Set[str] = set(self.selected_files)
        added = 0
        for p in paths:
            ap = os.path.abspath(p)
            if os.path.isfile(ap) and ap not in seen:
                self.selected_files.append(ap)
                self.listbox.insert(tk.END, ap)
                seen.add(ap)
                added += 1
        self._log(f"추가된 파일: {added}개")

    def _log(self, msg: str) -> None:
        self.log.insert(tk.END, msg + "\n")
        self.log.see(tk.END)

    def check_env(self) -> None:
        info = load_env(verbose=False)
        self._log("[환경] 작업 디렉토리: " + info.get("cwd", ""))
        self._log("[환경] 프로젝트 루트: " + info.get("root", ""))
        env_files = info.get("loaded_env_files", [])
        if env_files:
            self._log("[환경] 로드된 .env:")
            for p in env_files:
                self._log("  - " + p)
        else:
            self._log("[환경] 로드된 .env 없음 (CWD/루트 확인)")
        self._log("[환경] OPENAI_API_KEY: " + info.get("OPENAI_API_KEY", ""))
        self._log("[환경] ANTHROPIC_API_KEY: " + info.get("ANTHROPIC_API_KEY", ""))
        self._log("[환경] OPENAI_BASE_URL: " + info.get("OPENAI_BASE_URL", ""))
        self._log("[환경] ANTHROPIC_BASE_URL: " + info.get("ANTHROPIC_BASE_URL", ""))

    def start_generation(self) -> None:
        # Fixed settings
        provider = "anthropic"
        model = "claude-sonnet-4-5"
        lang = "ko"
        max_tokens = 10000
        temperature = 0.9

        # User inputs
        keyword = self.keyword.get().strip()
        topic = self.topic.get().strip()
        word_count = self._safe_int(self.word_count.get(), 1000)
        out_path = self.out_path.get().strip()

        # Build purpose from keyword, topic, word count
        if not keyword and not topic:
            messagebox.showwarning("입력 필요", "키워드 또는 주제를 입력해주세요.")
            return

        # Create purpose string with style guide
        purpose_parts = []
        if keyword:
            purpose_parts.append(f'"{keyword}" 키워드로')
        if topic:
            purpose_parts.append(f'{topic}에 대한')
        purpose_parts.append(f'블로그 글 {word_count}자 작성해줘.')

        # Add style guide
        style_guide = '''
**절대 하지 말아야 할 것:**
- 불릿 포인트(-), 번호 리스트(1. 2. 3.) 사용 금지
- 표, 체크박스 사용 금지
- H2, H3 같은 헤더 표시 금지
- SEO 메타 설명, 핵심 키워드, 추천 슬러그 같은 기술적 요소 전부 제거
- "다음과 같습니다", "아래를 참고하세요" 같은 딱딱한 표현 금지

**작성 방식:**
- 모든 내용을 자연스러운 문단으로 풀어서 설명
- "첫 번째로", "두 번째로" 대신 "우선", "그리고", "또한" 같은 자연스러운 연결어 사용
- 여러 가지를 설명할 때도 리스트 없이 문장으로 이어서 작성

예시:
❌ 나쁜 예: "공진단이 필요한 분들은 다음과 같습니다:
- 만성피로에 시달리는 직장인
- 수험생"

✅ 좋은 예: "공진단은 특히 만성피로에 시달리시는 직장인분들, 그리고 장시간 공부하느라 체력이 떨어진 수험생분들께 도움이 될 수 있어요."
'''

        purpose = ' '.join(purpose_parts) + style_guide

        if not out_path:
            messagebox.showwarning("출력 경로", "출력 파일 경로를 지정해주세요.")
            return

        self.status_var.set("생성 중… 잠시만 기다려주세요")
        self._log("[단계] 첨부 스캔 시작")
        btn_state = {}
        for child in self.winfo_children():
            try:
                state = child["state"]
                btn_state[child] = state
                child.configure(state=tk.DISABLED)
            except Exception:
                pass

        def task():
            import time
            import traceback
            t0 = time.perf_counter()

            try:
                # Log user inputs
                self._log(f"키워드: {keyword}")
                self._log(f"주제: {topic}")
                self._log(f"목표 글자수: {word_count}자")
                self._log(f"생성된 프롬프트: {purpose}")

                # Expand directories already to file list; pass via patterns to run (works for explicit paths)
                files = list(self.selected_files)
                self._log(f"모델: {model}, 언어: {lang}, 첨부파일: {len(files)}개")

                # 첨부 파일 목록 상세 출력
                for i, f in enumerate(files, 1):
                    self._log(f"  파일 {i}: {f}")

                t1 = time.perf_counter()
                self._log(f"[단계] 프롬프트 구성/호출 준비 (경과 {t1 - t0:.2f}s)")
                self._log("[단계] API 호출 시작 (max_tokens=10000)")

                # Convert empty model string to None
                final_model = model if model else None

                cli_run(
                    provider=provider,
                    model=final_model,
                    purpose=purpose,
                    input_dir=None,
                    files=files,
                    out_path=out_path,
                    language=lang,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    debug=False,
                    log_callback=self._log,  # GUI 로그로 직접 출력
                )
                t2 = time.perf_counter()
                self._log(f"[단계] 완료 (총 {t2 - t0:.2f}s)")
                self.status_var.set("완료")
                messagebox.showinfo("완료", f"생성 완료: {out_path}")
            except Exception as e:
                self._log(f"오류 발생: {type(e).__name__}")
                self._log(f"오류 메시지: {str(e)}")
                self._log(f"상세 정보:\n{traceback.format_exc()}")
                self.status_var.set("오류 발생")
                messagebox.showerror("오류", str(e))
            finally:
                for w, st in btn_state.items():
                    try:
                        w.configure(state=st)
                    except Exception:
                        pass

        threading.Thread(target=task, daemon=True).start()

    @staticmethod
    def _safe_int(s: str, default: int) -> int:
        try:
            return int(s)
        except Exception:
            return default

    @staticmethod
    def _safe_float(s: str, default: float) -> float:
        try:
            return float(s)
        except Exception:
            return default

    def ping_provider(self) -> None:
        self._log("[연결 테스트] Provider=anthropic (claude-sonnet-4-5)")
        try:
            try:
                from .providers.anthropic_client import AnthropicClient  # type: ignore
            except Exception:
                import sys
                sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from src.providers.anthropic_client import AnthropicClient  # type: ignore
            msg = AnthropicClient().ping()
            self._log("[연결 테스트] 결과: " + msg)
            messagebox.showinfo("연결 테스트", msg)
        except Exception as e:
            self._log("[연결 테스트] 실패: " + str(e))
            messagebox.showerror("연결 테스트", str(e))

    def quick_chat_test(self) -> None:
        self._log("[짧은 생성 테스트] Provider=anthropic (claude-sonnet-4-5)")
        try:
            try:
                from .providers.anthropic_client import AnthropicClient  # type: ignore
            except Exception:
                import sys
                sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from src.providers.anthropic_client import AnthropicClient  # type: ignore
            msg = AnthropicClient().quick_chat_test()
            self._log("[짧은 생성 테스트] 결과: " + msg)
            messagebox.showinfo("짧은 생성 테스트", msg)
        except Exception as e:
            self._log("[짧은 생성 테스트] 실패: " + str(e))
            messagebox.showerror("짧은 생성 테스트", str(e))


def main() -> None:
    app = BlogDraftGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
