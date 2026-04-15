@echo off
REM Claude Desktop launcher. Resolves the MSIX install path so it survives updates.
REM Set ANTHROPIC_* so any bundled Claude Code subprocess inherits them.
REM Copy to a directory on PATH (e.g. %USERPROFILE%\Scripts).
REM Pair with: claude-desktop-3p.py enable    (registry policy for the chat UI)
set ANTHROPIC_BASE_URL=http://localhost:1235
set ANTHROPIC_AUTH_TOKEN=lmstudio
set ANTHROPIC_MODEL=qwen3.5-35b-a3b
set DEFAULT_LLM_MODEL=qwen3.5-35b-a3b
set DISABLE_PROMPT_CACHING=1
set CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1
set CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS=1
set CLAUDE_CODE_ATTRIBUTION_HEADER=0
set CLAUDE_CODE_USE_POWERSHELL_TOOL=1
set CLAUDE_CODE_MAX_OUTPUT_TOKENS=8192
set BASH_DEFAULT_TIMEOUT_MS=1800000
set BASH_MAX_TIMEOUT_MS=3600000
set ENABLE_TOOL_SEARCH=false

REM Uncomment to capture verbose 3P / OAuth / account flow in main.log:
REM set DESKTOP_LOG_LEVEL=debug
REM set CLAUDE_ENABLE_LOGGING=1
REM set DEBUG=custom-3p:*,account:*,oauth:*

for /f "usebackq delims=" %%i in (`powershell -NoProfile -Command "(Get-AppxPackage -Name 'Claude').InstallLocation"`) do set CLAUDE_DIR=%%i
if not defined CLAUDE_DIR (
  echo Claude Desktop not installed.
  exit /b 1
)
start "" "%CLAUDE_DIR%\app\claude.exe" %*
