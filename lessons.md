# Lessons Learned

> Running log of mistakes, wrong assumptions, and how they were fixed.
> One entry per lesson, short and concrete.

---

### L-001: Use NVIDIA Nemotron instead of OpenAI
- **What happened:** Plan originally specified GPT-4o-mini. User pointed out NVIDIA Nemotron-3-nano-omni-30b-a3b-reasoning is free and multimodal.
- **Fix:** Switched to `langchain_nvidia_ai_endpoints.ChatNVIDIA`. Updated all env vars from `OPENAI_API_KEY` to `NVIDIA_API_KEY`.
- **Takeaway:** Always check for free-tier LLM options before defaulting to paid ones. NVIDIA AI Endpoints offer competitive models at zero cost.

### L-002: Use cmd, NOT PowerShell
- **What happened:** Antigravity IDE defaults to PowerShell. PowerShell uses `;` instead of `&&`, has different quoting rules, and caused a failed `git commit` in Phase 1.
- **Fix:** Prefix ALL terminal commands with `cmd /c` to force cmd.exe execution. Example: `cmd /c "git add . && git commit -m \"message\""`.
- **Takeaway:** Every model touching this project MUST use `cmd /c` prefix for all commands. Do NOT use PowerShell syntax.


