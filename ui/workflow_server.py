import json
import os
import re
import signal
import subprocess
import threading
import time
from html import escape as html_escape
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse


PROJECT_ROOT = Path(__file__).resolve().parents[1]
UI_FILE = PROJECT_ROOT / "ui" / "workflow_app.html"
UI_UTILS_FILE = PROJECT_ROOT / "ui" / "workflow_app_utils.js"
RECOVERY_FILE = PROJECT_ROOT / "02_Research" / "workflow_recovery.json"
RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
MARKDOWN_LINK_WITH_SCHEME_PATTERN = re.compile(r"\]\(\s*([a-zA-Z][a-zA-Z0-9+.-]*):[^\n]*\)", re.IGNORECASE)
ALLOWED_LINK_PROTOCOLS = {"http", "https"}
STATUS_ALIASES = {"success": "done", "failed": "error"}
RUN_STATUSES = {"idle", "pending", "running", "paused", "done", "error", "unknown"}
STEP_STATUSES = {"pending", "running", "done", "error"}


def slugify(topic: str) -> str:
    topic = topic.strip().lower()
    topic = re.sub(r"[^a-z0-9\s_-]", "", topic)
    topic = re.sub(r"\s+", "_", topic)
    topic = re.sub(r"_+", "_", topic)
    return topic or "untitled"


@dataclass
class AppState:
    lock: threading.Lock = field(default_factory=threading.Lock)
    process: subprocess.Popen | None = None
    status: str = "idle"
    topic: str = ""
    logs: list[str] = field(default_factory=list)
    run_id: str = ""
    error_code: str = ""
    started_at: float = 0.0
    paused: bool = False
    exit_code: int | None = None
    result: dict = field(default_factory=dict)
    last_payload: dict = field(default_factory=dict)


STATE = AppState()
VALID_STATUS_TRANSITIONS = {
    "idle": {"running"},
    "running": {"paused", "done", "error", "idle"},
    "paused": {"running", "idle", "error"},
    "done": {"running", "idle"},
    "error": {"running", "idle"},
}


def can_transition(current: str, target: str) -> bool:
    return target in VALID_STATUS_TRANSITIONS.get(current, set())


def normalize_status(value: str, allowed: set[str], fallback: str) -> str:
    raw = str(value or "").strip().lower()
    mapped = STATUS_ALIASES.get(raw, raw)
    return mapped if mapped in allowed else fallback


def sanitize_markdown_preview(content: str) -> str:
    escaped = html_escape(str(content or ""), quote=False).replace("\x00", "")

    def _replace_link(match: re.Match) -> str:
        scheme = str(match.group(1) or "").lower()
        if scheme in ALLOWED_LINK_PROTOCOLS:
            return match.group(0)
        return "](#)"

    return MARKDOWN_LINK_WITH_SCHEME_PATTERN.sub(_replace_link, escaped)


def get_ui_config() -> dict:
    return {
        "run_statuses": sorted(RUN_STATUSES),
        "step_statuses": sorted(STEP_STATUSES),
        "status_aliases": dict(STATUS_ALIASES),
        "link_protocols": sorted(ALLOWED_LINK_PROTOCOLS),
    }


def infer_current_step(steps):
    for step in steps:
        if step.get("status") in {"running", "error"}:
            return str(step.get("id", ""))
    for step in reversed(steps):
        if step.get("status") == "done":
            return str(step.get("id", ""))
    return ""


def save_recovery(topic: str, payload: dict, status: str, steps: list[dict]):
    RECOVERY_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "topic": topic,
        "status": status,
        "last_step": infer_current_step(steps),
        "payload": payload if isinstance(payload, dict) else {},
        "updated_at": int(time.time()),
    }
    RECOVERY_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_recovery():
    if not RECOVERY_FILE.exists():
        return {}
    try:
        data = json.loads(RECOVERY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def parse_line(line: str):
    run_match = re.search(r"run_id=([a-f0-9-]+)", line)
    code_match = re.search(r"code=([A-Z_]+)", line)
    if run_match:
        STATE.run_id = run_match.group(1)
    if code_match:
        STATE.error_code = code_match.group(1)


def append_log(line: str):
    with STATE.lock:
        STATE.logs.append(line.rstrip("\n"))
        if len(STATE.logs) > 2000:
            STATE.logs = STATE.logs[-2000:]
        parse_line(line)


def read_output():
    proc = STATE.process
    if not proc or not proc.stdout:
        return
    for line in proc.stdout:
        append_log(line)


def compute_steps(log_text: str, status: str):
    steps = [
        {"id": "research", "name": "Research", "status": "pending"},
        {"id": "analysis", "name": "Analysis", "status": "pending"},
        {"id": "knowledge", "name": "Knowledge", "status": "pending"},
        {"id": "writer", "name": "Writer", "status": "pending"},
    ]
    research_done = "Research completed" in log_text
    analysis_started = "Prepare NotebookLM sources" in log_text
    analysis_done = "NotebookLM prompt generated" in log_text
    writer_done = "Note created" in log_text or "Failure metadata written" in log_text

    if status in ("running", "paused"):
        if not research_done:
            steps[0]["status"] = "running"
        else:
            steps[0]["status"] = "done"
            if not analysis_done:
                steps[1]["status"] = "running" if analysis_started else "pending"
            else:
                steps[1]["status"] = "done"
                if not writer_done:
                    steps[2]["status"] = "running"
                else:
                    steps[2]["status"] = "done"
                    steps[3]["status"] = "done"
    elif status == "done":
        for s in steps:
            s["status"] = "done"
    elif status == "error":
        if research_done:
            steps[0]["status"] = "done"
        else:
            steps[0]["status"] = "error"
        if analysis_done:
            steps[1]["status"] = "done"
        elif analysis_started:
            steps[1]["status"] = "error"
        if writer_done:
            steps[3]["status"] = "error"

    done_count = sum(1 for s in steps if s["status"] == "done")
    progress = int(done_count / len(steps) * 100)
    return steps, progress


def read_run_result(topic: str):
    run_path = PROJECT_ROOT / "02_Research" / f"{slugify(topic)}.run.json"
    if run_path.exists():
        try:
            return json.loads(run_path.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def read_notebooklm_session(topic: str):
    path = PROJECT_ROOT / "02_Research" / "notebooklm_session.json"
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if str(payload.get("topic", "")).strip() != topic:
        return {}
    notebook_id = str(payload.get("notebook_id", "")).strip()
    payload["notebook_url"] = str(payload.get("notebook_url") or (f"https://notebooklm.google.com/notebook/{notebook_id}" if notebook_id else ""))
    return payload


def normalize_result_contract(topic: str, result: dict):
    payload = result if isinstance(result, dict) else {}
    payload.setdefault("schema_version", "1.1")
    payload.setdefault("status", "")
    payload.setdefault("source_count", 0)
    payload.setdefault("artifacts", {})
    if not isinstance(payload.get("artifacts"), dict):
        payload["artifacts"] = {}

    notebooklm = payload.get("notebooklm", {})
    if not isinstance(notebooklm, dict):
        notebooklm = {}

    session = read_notebooklm_session(topic)
    notebook_id = str(notebooklm.get("notebook_id") or session.get("notebook_id") or "")
    notebook_url = str(notebooklm.get("notebook_url") or session.get("notebook_url") or (f"https://notebooklm.google.com/notebook/{notebook_id}" if notebook_id else ""))
    payload["notebooklm"] = {"notebook_id": notebook_id, "notebook_url": notebook_url}
    return payload


def finalize_process():
    proc = STATE.process
    if not proc:
        return
    code = proc.wait()
    with STATE.lock:
        STATE.exit_code = code
        STATE.result = normalize_result_contract(STATE.topic, read_run_result(STATE.topic))
        next_status = "done" if code == 0 else "error"
        if STATE.status != "idle" and can_transition(STATE.status, next_status):
            STATE.status = next_status
        if code != 0 and not STATE.error_code:
            STATE.error_code = "UNEXPECTED_ERROR"
        current_status = STATE.status
        current_topic = STATE.topic
        current_payload = STATE.last_payload
        log_text = "\n".join(STATE.logs)
        STATE.process = None
        STATE.paused = False

    steps, _ = compute_steps(log_text, current_status)
    save_recovery(current_topic, current_payload, current_status, steps)


def python_bin():
    venv_py = PROJECT_ROOT / ".venv" / "bin" / "python"
    return str(venv_py) if venv_py.exists() else "python3"


def start_run(payload: dict):
    topic = str(payload.get("topic", "")).strip()
    if not topic:
        return 400, {"error": "topic is required"}

    safe_payload = {
        "topic": topic,
        "max_results": int(payload.get("max_results", 5)),
        "timeout_seconds": int(payload.get("timeout_seconds", 20)),
        "retries": int(payload.get("retries", 3)),
        "log_format": str(payload.get("log_format", "plain")),
        "notebooklm_auto_analyze": bool(payload.get("notebooklm_auto_analyze", False)),
        "notebooklm_home": str(payload.get("notebooklm_home", "")).strip(),
    }

    with STATE.lock:
        if STATE.process and STATE.status in ("running", "paused"):
            return 409, {"error": "process already running"}
        if not can_transition(STATE.status, "running"):
            return 409, {"error": f"invalid state transition: {STATE.status} -> running"}

        STATE.topic = topic
        STATE.logs = []
        STATE.run_id = ""
        STATE.error_code = ""
        STATE.result = {}
        STATE.exit_code = None
        STATE.started_at = time.time()
        STATE.status = "running"
        STATE.paused = False
        STATE.last_payload = safe_payload

        env = os.environ.copy()
        env["YOUTUBE_MAX_RESULTS"] = str(safe_payload.get("max_results", 5))
        env["YOUTUBE_TIMEOUT_SECONDS"] = str(safe_payload.get("timeout_seconds", 20))
        env["YOUTUBE_RETRIES"] = str(safe_payload.get("retries", 3))
        env["LOG_FORMAT"] = str(safe_payload.get("log_format", "plain"))
        env["NOTEBOOKLM_AUTO_ANALYZE"] = str(safe_payload.get("notebooklm_auto_analyze", False)).lower()
        notebooklm_home = str(safe_payload.get("notebooklm_home", "")).strip()
        if notebooklm_home:
            env["NOTEBOOKLM_HOME"] = notebooklm_home

        cmd = [python_bin(), "-m", "agents.research", topic]
        proc = subprocess.Popen(
            cmd,
            cwd=str(PROJECT_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env,
        )
        STATE.process = proc

    threading.Thread(target=read_output, daemon=True).start()
    threading.Thread(target=finalize_process, daemon=True).start()
    steps, _ = compute_steps("", "running")
    save_recovery(topic, safe_payload, "running", steps)
    return 200, {"ok": True}


def retry_current_step():
    with STATE.lock:
        if STATE.process and STATE.status in ("running", "paused"):
            return 409, {"error": "process is running"}
        payload = STATE.last_payload if isinstance(STATE.last_payload, dict) else {}

    if not payload:
        recovered = load_recovery()
        candidate = recovered.get("payload", {}) if isinstance(recovered, dict) else {}
        payload = candidate if isinstance(candidate, dict) else {}

    if not payload or not str(payload.get("topic", "")).strip():
        return 409, {"error": "no recovery payload"}

    return start_run(payload)


def pause_run():
    with STATE.lock:
        if not STATE.process or STATE.status != "running":
            return 409, {"error": "process is not running"}
        if not can_transition(STATE.status, "paused"):
            return 409, {"error": f"invalid state transition: {STATE.status} -> paused"}
        os.kill(STATE.process.pid, signal.SIGSTOP)
        STATE.status = "paused"
        STATE.paused = True
    return 200, {"ok": True}


def resume_run():
    with STATE.lock:
        if not STATE.process or STATE.status != "paused":
            return 409, {"error": "process is not paused"}
        if not can_transition(STATE.status, "running"):
            return 409, {"error": f"invalid state transition: {STATE.status} -> running"}
        os.kill(STATE.process.pid, signal.SIGCONT)
        STATE.status = "running"
        STATE.paused = False
    return 200, {"ok": True}


def reset_run():
    with STATE.lock:
        proc = STATE.process
    if proc:
        try:
            proc.terminate()
            proc.wait(timeout=3)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

    with STATE.lock:
        STATE.process = None
        STATE.status = "idle"
        STATE.topic = ""
        STATE.logs = []
        STATE.run_id = ""
        STATE.error_code = ""
        STATE.started_at = 0.0
        STATE.paused = False
        STATE.exit_code = None
        STATE.result = {}
    save_recovery("", {}, "idle", [])
    return 200, {"ok": True}


def get_state():
    with STATE.lock:
        log_text = "\n".join(STATE.logs)
        status = normalize_status(STATE.status, RUN_STATUSES, "unknown")
        steps, progress = compute_steps(log_text, status)
        elapsed = int(time.time() - STATE.started_at) if STATE.started_at else 0
        result = normalize_result_contract(STATE.topic, STATE.result)
        topic = STATE.topic
        payload = STATE.last_payload
        run_id = STATE.run_id
        error_code = STATE.error_code
        logs = STATE.logs[-300:]

    save_recovery(topic, payload, status, steps)
    recovered = load_recovery()
    can_retry = status in {"error", "done", "idle"} and bool(payload or recovered.get("payload"))

    return {
        "status": status,
        "topic": topic,
        "run_id": run_id,
        "error_code": error_code,
        "elapsed_seconds": elapsed,
        "steps": steps,
        "progress": progress,
        "logs": logs,
        "result": result,
        "recovery": {
            "can_retry": can_retry,
            "last_step": infer_current_step(steps) or str(recovered.get("last_step", "")),
            "checkpoint_status": normalize_status(str(recovered.get("status", status)), RUN_STATUSES, "unknown"),
        },
    }


def get_history_runs():
    directory = PROJECT_ROOT / "02_Research"
    if not directory.exists():
        return []
        
    runs = []
    for file in directory.glob("*.run.json"):
        try:
            data = json.loads(file.read_text(encoding="utf-8"))
            if "run_id" in data and "topic" in data:
                # 尝试获取对应 markdown 文件的修改时间作为生成时间
                mtime = file.stat().st_mtime
                data["_mtime"] = mtime
                runs.append(data)
        except Exception:
            continue
            
    # 按时间倒序排序
    runs.sort(key=lambda x: x.get("_mtime", 0), reverse=True)
    
    # 清理辅助排序字段
    for r in runs:
        r.pop("_mtime", None)
        
    return runs


def get_artifact_content(run_id: str):
    if not isinstance(run_id, str) or not RUN_ID_PATTERN.fullmatch(run_id):
        return 400, {"error": "invalid run_id"}

    runs = get_history_runs()
    target_run = next((r for r in runs if r.get("run_id") == run_id), None)

    if not target_run:
        return 404, {"error": "run not found"}

    md_path = target_run.get("artifacts", {}).get("markdown")
    if not isinstance(md_path, str) or not md_path.strip():
        return 404, {"error": "markdown artifact not found in run"}

    full_path = (PROJECT_ROOT / md_path).resolve()
    project_root = PROJECT_ROOT.resolve()
    if full_path != project_root and project_root not in full_path.parents:
        return 400, {"error": "invalid artifact path"}

    if not full_path.exists():
        return 404, {"error": f"file not found: {md_path}"}

    try:
        content = full_path.read_text(encoding="utf-8")
        return 200, {
            "content": content,
            "preview_content": sanitize_markdown_preview(content),
            "run": target_run,
            "filename": full_path.name,
        }
    except Exception as e:
        return 500, {"error": str(e)}


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, code, payload):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw) if raw else {}

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            if not UI_FILE.exists():
                self.send_error(404, "workflow_app.html not found")
                return
            content = UI_FILE.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return
        if path == "/workflow_app_utils.js":
            if not UI_UTILS_FILE.exists():
                self.send_error(404, "workflow_app_utils.js not found")
                return
            content = UI_UTILS_FILE.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/javascript; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return
        if path == "/api/ui-config":
            self._send_json(200, get_ui_config())
            return
        if path == "/api/state":
            self._send_json(200, get_state())
            return
        if path == "/api/runs":
            self._send_json(200, {"runs": get_history_runs()})
            return
        if path.startswith("/api/runs/") and path.endswith("/artifact/download"):
            run_id = unquote(path.split("/")[3])
            code, res = get_artifact_content(run_id)
            if code != 200:
                self._send_json(code, res)
                return
            content = res.get("content", "")
            filename = str(res.get("filename", "artifact.md")).replace('"', "")
            data = str(content).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/markdown; charset=utf-8")
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if path.startswith("/api/runs/") and path.endswith("/artifact"):
            run_id = unquote(path.split("/")[3])
            code, res = get_artifact_content(run_id)
            self._send_json(code, res)
            return
        self.send_error(404, "Not Found")

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            payload = self._read_json()
        except Exception:
            self._send_json(400, {"error": "invalid json"})
            return

        if path == "/api/start":
            code, res = start_run(payload)
            self._send_json(code, res)
            return
        if path == "/api/pause":
            code, res = pause_run()
            self._send_json(code, res)
            return
        if path == "/api/resume":
            code, res = resume_run()
            self._send_json(code, res)
            return
        if path == "/api/reset":
            code, res = reset_run()
            self._send_json(code, res)
            return
        if path == "/api/retry-step":
            code, res = retry_current_step()
            self._send_json(code, res)
            return

        self.send_error(404, "Not Found")


if __name__ == "__main__":
    port = int(os.getenv("WORKFLOW_UI_PORT", "8765"))
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Workflow UI: http://127.0.0.1:{port}")
    server.serve_forever()
