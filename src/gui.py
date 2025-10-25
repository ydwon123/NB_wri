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
        # Input Fields: Keyword, Keyword Repeat, Word Count (in one row)
        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=10, pady=8)

        ttk.Label(top, text="키워드").grid(row=0, column=0, sticky=tk.W, padx=(0, 6))
        self.keyword = ttk.Entry(top, width=30)
        self.keyword.grid(row=0, column=1, sticky=tk.W)

        ttk.Label(top, text="키워드 반복").grid(row=0, column=2, sticky=tk.W, padx=(16, 6))
        self.keyword_repeat = ttk.Entry(top, width=12)
        self.keyword_repeat.insert(0, "5")
        self.keyword_repeat.grid(row=0, column=3, sticky=tk.W)

        ttk.Label(top, text="글자수").grid(row=0, column=4, sticky=tk.W, padx=(16, 6))
        self.word_count = ttk.Entry(top, width=12)
        self.word_count.insert(0, "1000")
        self.word_count.grid(row=0, column=5, sticky=tk.W)

        # Writing Guide (Required - replaces topic)
        guide_fr = ttk.LabelFrame(self, text="주제 및 가이드")
        guide_fr.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

        guide_scroll = ttk.Scrollbar(guide_fr)
        guide_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.writing_guide_text = tk.Text(guide_fr, height=10, yscrollcommand=guide_scroll.set)
        self.writing_guide_text.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        guide_scroll.config(command=self.writing_guide_text.yview)

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
        word_count = self._safe_int(self.word_count.get(), 1000)
        keyword_repeat = self._safe_int(self.keyword_repeat.get(), 5)
        out_path = self.out_path.get().strip()
        writing_guide = self.writing_guide_text.get("1.0", tk.END).strip()

        # Validation
        if not writing_guide:
            messagebox.showwarning("입력 필요", "주제 및 가이드를 입력해주세요.")
            return

        if not keyword:
            messagebox.showwarning("입력 필요", "키워드를 입력해주세요.")
            return

        if not out_path:
            messagebox.showwarning("출력 경로", "출력 파일 경로를 지정해주세요.")
            return

        self.status_var.set("생성 중… 잠시만 기다려주세요")
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
                self._log(f"목표 글자수: {word_count}자")
                self._log(f"키워드 반복 횟수: {keyword_repeat}회")
                self._log(f"주제 및 가이드: {writing_guide[:100]}..." if len(writing_guide) > 100 else f"주제 및 가이드: {writing_guide}")

                # Expand directories already to file list; pass via patterns to run (works for explicit paths)
                files = list(self.selected_files)
                self._log(f"모델: {model}, 언어: {lang}, 첨부파일: {len(files)}개")

                # 첨부 파일 목록 상세 출력
                for i, f in enumerate(files, 1):
                    self._log(f"  파일 {i}: {f}")

                # Convert empty model string to None
                final_model = model if model else None

                cli_run(
                    provider=provider,
                    model=final_model,
                    keyword=keyword,
                    keyword_repeat=keyword_repeat,
                    input_dir=None,
                    files=files,
                    out_path=out_path,
                    language=lang,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    debug=False,
                    log_callback=self._log,  # GUI 로그로 직접 출력
                    writing_guide=writing_guide,
                )
                t2 = time.perf_counter()
                self._log(f"[완료] 총 소요 시간: {t2 - t0:.2f}s")
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
