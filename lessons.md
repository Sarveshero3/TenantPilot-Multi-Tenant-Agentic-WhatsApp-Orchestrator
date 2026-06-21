# Lessons Learned

> Running log of mistakes, wrong assumptions, and how they were fixed.
> One entry per lesson, short and concrete.

---

### L-001: Use NVIDIA Nemotron instead of OpenAI
- **What happened:** Plan originally specified GPT-4o-mini. User pointed out NVIDIA Nemotron-3-nano-omni-30b-a3b-reasoning is free and multimodal.
- **Fix:** Switched to `langchain_nvidia_ai_endpoints.ChatNVIDIA`. Updated all env vars from `OPENAI_API_KEY` to `NVIDIA_API_KEY`.
- **Takeaway:** Always check for free-tier LLM options before defaulting to paid ones. NVIDIA AI Endpoints offer competitive models at zero cost.

### L-002: Use cmd, NOT PowerShell
- **What happened:** Antigravity IDE defaults to PowerShell. PowerShell uses `;` instead of `&&`, has different quoting rules, and caused failed commands in Phase 1.
- **Fix:** Prefix ALL terminal commands with `cmd /c`. But **DO NOT chain commands with escaped quotes** — the escaping breaks when PowerShell passes to cmd. Instead, run `git add` and `git commit` as **separate** `cmd /c` calls. For commit messages, use **hyphens instead of spaces** to avoid quoting issues entirely.
- **Working pattern:**
  ```
  cmd /c "git add ."
  cmd /c "git commit -m my-commit-message-no-spaces"
  ```
- **Takeaway:** Every model touching this project MUST use `cmd /c` prefix. Keep commit messages hyphenated (no spaces, no quotes).

### L-003: Python 3.14 — use latest package versions, not pinned older ones
- **What happened:** `requirements.txt` pinned `beanie==1.27.0` and `pydantic==2.10.3`. Python 3.14 has no prebuilt wheels for those. pip tried to build from source and failed (missing zlib for Pillow).
- **Fix:** Let pip resolve the latest compatible versions. The installed versions are: `beanie==2.0.0`, `pydantic==2.13.4`, `fastapi==0.138.0`, `motor==3.7.1`, `uvicorn==0.49.0`. Updated `requirements.txt` to unpinned minimums.
- **Takeaway:** On Python 3.14 (cutting-edge), always use `>=` bounds or no version pins, not `==` exact pins for packages that need compiled extensions.




