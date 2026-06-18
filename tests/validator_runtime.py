"""Shared validator lifecycle utilities for tests."""

import json
import os
import signal
import shutil
import subprocess
import tempfile
import time
import urllib.request
from contextlib import suppress
from pathlib import Path
from typing import NamedTuple

_VALIDATOR_ARGS = [
    "--reset",
    "--rpc-pubsub-enable-vote-subscription",
    "--quiet",
]

_SHARED_RUNTIME_DIR = Path(tempfile.gettempdir()) / "solana-py-validator-shared"
_SHARED_STATE_FILE = _SHARED_RUNTIME_DIR / "state.json"
_SHARED_LOCK_DIR = _SHARED_RUNTIME_DIR / "lock"


class ValidatorConfig(NamedTuple):
    """Runtime configuration for a single validator instance."""

    rpc_url: str
    ws_url: str
    worker_id: str
    rpc_port: int
    ledger_dir: str


def env_int(name: str, default: int) -> int:
    """Read an integer environment variable with a fallback default."""
    try:
        return int(os.environ.get(name, str(default)))
    except (TypeError, ValueError):
        return default


def _acquire_dir_lock(lock_dir: Path, timeout_secs: int = 120) -> None:
    """Acquire the validator lifecycle lock via mkdir.

    This lock protects shared validator lifecycle state (pid/refcount/state file)
    and does not serialize RPC or websocket request traffic.
    """
    deadline = time.time() + timeout_secs
    lock_dir.parent.mkdir(parents=True, exist_ok=True)
    while time.time() < deadline:
        try:
            lock_dir.mkdir()
            return
        except FileExistsError:
            with suppress(FileNotFoundError):
                stale_after = 300
                if time.time() - lock_dir.stat().st_mtime > stale_after:
                    lock_dir.rmdir()
                    continue
            time.sleep(0.1)
    raise RuntimeError(f"Timeout acquiring validator lifecycle lock: {lock_dir}")


def _release_dir_lock(lock_dir: Path) -> None:
    """Release validator lifecycle lock acquired by _acquire_dir_lock."""
    with suppress(FileNotFoundError, OSError):
        lock_dir.rmdir()


def _process_is_alive(pid: int) -> bool:
    """Return True if a process exists."""
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _read_shared_state() -> dict | None:
    """Read validator shared state from disk."""
    if not _SHARED_STATE_FILE.exists():
        return None
    try:
        return json.loads(_SHARED_STATE_FILE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def _write_shared_state(state: dict) -> None:
    """Persist validator shared state."""
    _SHARED_RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    _SHARED_STATE_FILE.write_text(json.dumps(state), encoding="utf-8")


def _remove_shared_state() -> None:
    """Delete shared state file."""
    with suppress(FileNotFoundError):
        _SHARED_STATE_FILE.unlink()


def _stop_pid(pid: int) -> None:
    """Gracefully stop a process by PID with SIGTERM then SIGKILL fallback."""
    if not _process_is_alive(pid):
        return
    with suppress(ProcessLookupError):
        os.kill(pid, signal.SIGTERM)
    deadline = time.time() + 10
    while time.time() < deadline:
        if not _process_is_alive(pid):
            return
        time.sleep(0.1)
    with suppress(ProcessLookupError):
        os.kill(pid, signal.SIGKILL)


def tail_file(path: Path, max_lines: int = 30) -> str:
    """Read the last few lines from a text file for error diagnostics."""
    if not path.exists():
        return ""
    with path.open("r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    return "".join(lines[-max_lines:])


def validator_is_healthy(rpc_url: str) -> bool:
    """Return True when an RPC endpoint responds healthy."""
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "getHealth"}).encode()
    try:
        req = urllib.request.Request(
            rpc_url,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=2) as resp:
            return json.loads(resp.read()).get("result") == "ok"
    except Exception:  # noqa: BLE001
        return False


def _launch_shared_validator(rpc_port: int, rpc_url: str, ws_url: str) -> dict:
    """Start a new shared validator process and return persisted state."""
    ledger_dir = tempfile.mkdtemp(prefix="solana-test-ledger-shared-")
    validator_log_path = Path(ledger_dir) / "validator.log"
    validator_args = [
        "solana-test-validator",
        *_VALIDATOR_ARGS,
        "--ledger",
        ledger_dir,
        "--rpc-port",
        str(rpc_port),
        "--gossip-port",
        str(env_int("SOLANA_TEST_VALIDATOR_GOSSIP_PORT", 23000)),
        "--faucet-port",
        str(env_int("SOLANA_TEST_VALIDATOR_FAUCET_PORT", 24000)),
        "--dynamic-port-range",
        os.environ.get("SOLANA_TEST_VALIDATOR_DYNAMIC_PORT_RANGE", "20000-20099"),
    ]

    with validator_log_path.open("w", encoding="utf-8") as validator_log:
        proc = subprocess.Popen(
            validator_args,
            stdout=validator_log,
            stderr=validator_log,
        )

    deadline = time.time() + 60
    while time.time() < deadline:
        if validator_is_healthy(rpc_url):
            return {
                "pid": proc.pid,
                "rpc_url": rpc_url,
                "ws_url": ws_url,
                "rpc_port": rpc_port,
                "ledger_dir": ledger_dir,
                "refcount": 1,
            }
        if proc.poll() is not None:
            log_tail = tail_file(validator_log_path)
            raise RuntimeError(
                "shared solana-test-validator exited prematurely "
                f"(code {proc.returncode}) at {rpc_url}.\n"
                f"args={validator_args}\n"
                f"log_tail:\n{log_tail}"
            )
        time.sleep(1)

    proc.terminate()
    proc.wait(timeout=10)
    log_tail = tail_file(validator_log_path)
    raise RuntimeError(
        f"shared solana-test-validator did not become healthy within 60 s at {rpc_url}.\n"
        f"args={validator_args}\n"
        f"log_tail:\n{log_tail}"
    )


def acquire_shared_validator(worker_id: str) -> ValidatorConfig:
    """Get or start the shared validator and increment reference count."""
    base_rpc_port = env_int("SOLANA_TEST_VALIDATOR_BASE_RPC_PORT", 18899)
    rpc_port = base_rpc_port
    ws_port = rpc_port + 1
    rpc_url = f"http://127.0.0.1:{rpc_port}"
    ws_url = f"ws://127.0.0.1:{ws_port}"

    _acquire_dir_lock(_SHARED_LOCK_DIR)
    try:
        state = _read_shared_state() or {}
        pid = int(state.get("pid", 0))
        managed_ok = (
            bool(state)
            and _process_is_alive(pid)
            and validator_is_healthy(state.get("rpc_url", ""))
        )

        if managed_ok:
            state["refcount"] = int(state.get("refcount", 0)) + 1
            _write_shared_state(state)
        else:
            with suppress(Exception):
                _stop_pid(pid)
            old_ledger = state.get("ledger_dir", "")
            if old_ledger:
                shutil.rmtree(old_ledger, ignore_errors=True)
            state = _launch_shared_validator(
                rpc_port=rpc_port, rpc_url=rpc_url, ws_url=ws_url
            )
            _write_shared_state(state)

        return ValidatorConfig(
            rpc_url=state["rpc_url"],
            ws_url=state["ws_url"],
            worker_id=worker_id,
            rpc_port=int(state.get("rpc_port", rpc_port)),
            ledger_dir=state.get("ledger_dir", ""),
        )
    finally:
        _release_dir_lock(_SHARED_LOCK_DIR)


def release_shared_validator() -> None:
    """Decrement shared validator refcount and stop it when no users remain."""
    _acquire_dir_lock(_SHARED_LOCK_DIR)
    try:
        current = _read_shared_state()
        if not current:
            return

        refcount = max(0, int(current.get("refcount", 1)) - 1)
        current["refcount"] = refcount
        if refcount > 0:
            _write_shared_state(current)
            return

        pid = int(current.get("pid", 0))
        ledger_dir = current.get("ledger_dir", "")
        _stop_pid(pid)
        if ledger_dir:
            shutil.rmtree(ledger_dir, ignore_errors=True)
        _remove_shared_state()
    finally:
        _release_dir_lock(_SHARED_LOCK_DIR)
