#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BASKA SEND v2.0 - single-file Windows message/file hub.

Core features
- Modern responsive WebApp with Dark/Light Mode and Indonesian date/time.
- Main PIN + per-device PIN + one-time QR/code pairing + device revocation.
- Active-device list with online state, last active time, LAN IP and direct private chat.
- Private conversations, direct device-to-device messages, and Public / Ruang Umum.
- Message delivery states: Terkirim, Diterima, Dibuka, Dibalas.
- Reply/quote messages in WebApp and inline reply inside the same Windows popup.
- Send text and approved files; drag & drop and paste clipboard images in WebApp.
- Native modern popup, Windows-style dialog and Windows notification balloon.
- Popup countdown, custom sounds, Copy, Reply, Close and remote-close controls.
- File actions: internal image/text preview, Open file, Open folder and detailed metadata/hash.
- Configurable receive folder with automatic category organization (Images/PDF/Documents/etc.).
- Per-device delete of messages sent by that device; files on disk are preserved safely.
- Windows system tray: open WebApp/folder, copy URL, pause notifications, status, restart, exit.
- SQLite history, CSRF/session protections, login/pairing rate-limit, safe file allowlist/signature checks.
- Windows auto-start at user logon and optional Private-profile firewall rule.

First setup:
    python SendToCom.py --setup

Check status:
    python SendToCom.py --status
"""
from __future__ import annotations

import argparse
import base64
import ctypes
import datetime as _dt
import hashlib
import hmac
import ipaddress
import io
import json
import mimetypes
import os
import queue
import shutil
import re
import secrets
import socket
import sqlite3
import subprocess
import sys
import tempfile
import threading
import webbrowser
import time
import traceback
import urllib.parse
import uuid
import zipfile
from dataclasses import dataclass
from email.parser import BytesParser
from email.policy import default as email_default_policy
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

APP_NAME = "SendToCom"
APP_TITLE = "BASKA SEND"
VERSION = "2.2.4"
TASK_NAME = "SendToCom"
FIREWALL_RULE_NAME = "SendToCom"
LEGACY_APP_NAME = "PCMessageHub"
LEGACY_DISPLAY_NAME = "BASKA HUB"
LEGACY_TASK_NAME = "PC Message Hub"
LEGACY_FIREWALL_RULE_NAME = "PC Message Hub"
DEFAULT_PORT = 8765
MAX_BODY_OVERHEAD = 2 * 1024 * 1024
SESSION_COOKIE = "pcmh_session"
SESSION_HOURS = 24
PIN_ITERATIONS = 260_000

DEFAULT_ALLOWED_EXTENSIONS = [
    ".pdf", ".docx", ".xlsx", ".pptx",
    ".txt", ".csv",
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp",
]
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
PREVIEWABLE_EXTENSIONS = IMAGE_EXTENSIONS | {".pdf", ".txt", ".csv"}
DANGEROUS_EXTENSIONS = {
    ".exe", ".com", ".bat", ".cmd", ".ps1", ".vbs", ".vbe", ".js", ".jse",
    ".wsf", ".wsh", ".msi", ".msp", ".scr", ".pif", ".cpl", ".dll", ".sys",
    ".jar", ".lnk", ".reg", ".hta", ".html", ".htm", ".svg", ".docm", ".xlsm", ".pptm",
}

FAVICON_PNG = base64.b64decode("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")
FAVICON_ICO = base64.b64decode("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")


def _data_root(app_name: str) -> Path:
    root = os.environ.get("LOCALAPPDATA")
    if root:
        return Path(root) / app_name
    return Path.home() / f".{app_name.lower()}"


def _base_dir() -> Path:
    return _data_root(APP_NAME)


APP_DIR = _base_dir()
LEGACY_APP_DIR = _data_root(LEGACY_APP_NAME)
CONFIG_PATH = APP_DIR / "config.json"
DB_PATH = APP_DIR / "messages.db"
LEGACY_UPLOAD_DIR = APP_DIR / "uploads"
OUTBOX_DIR = APP_DIR / "outbox"
LOG_PATH = APP_DIR / "app.log"
FIRST_PIN_PATH = APP_DIR / "FIRST_RUN_PIN.txt"
MIGRATION_MARKER = APP_DIR / ".migrated_from_pcmessagehub"


def _migrate_legacy_data_once() -> None:
    """Safely copy legacy config/database once without deleting old data."""
    APP_DIR.mkdir(parents=True, exist_ok=True)
    if MIGRATION_MARKER.exists() or not LEGACY_APP_DIR.exists() or LEGACY_APP_DIR.resolve() == APP_DIR.resolve():
        return
    try:
        old_cfg = LEGACY_APP_DIR / "config.json"
        if old_cfg.exists() and not CONFIG_PATH.exists():
            shutil.copy2(str(old_cfg), str(CONFIG_PATH))

        old_db = LEGACY_APP_DIR / "messages.db"
        if old_db.exists() and not DB_PATH.exists():
            src_con = sqlite3.connect(str(old_db), timeout=15)
            dst_con = sqlite3.connect(str(DB_PATH), timeout=15)
            try:
                src_con.backup(dst_con)
            finally:
                dst_con.close()
                src_con.close()

        old_pin = LEGACY_APP_DIR / "FIRST_RUN_PIN.txt"
        if old_pin.exists() and not FIRST_PIN_PATH.exists():
            shutil.copy2(str(old_pin), str(FIRST_PIN_PATH))

        MIGRATION_MARKER.write_text(
            f"Migrated safely from {LEGACY_APP_DIR} on {now_iso() if 'now_iso' in globals() else _dt.datetime.now().isoformat()}\n",
            encoding="utf-8",
        )
    except Exception:
        # Never prevent startup because a legacy copy could not be completed.
        pass


def ensure_dirs() -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    _migrate_legacy_data_once()
    LEGACY_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    OUTBOX_DIR.mkdir(parents=True, exist_ok=True)


def default_received_files_dir() -> str:
    if os.name == "nt":
        return r"%USERPROFILE%\Downloads\BASKA SEND"
    return str(Path.home() / "Downloads" / "BASKA SEND")


def legacy_received_files_dir() -> Path:
    if os.name == "nt":
        raw = r"%USERPROFILE%\Downloads\BASKA HUB"
    else:
        raw = str(Path.home() / "Downloads" / "BASKA HUB")
    return Path(os.path.expandvars(raw)).expanduser().resolve()


def expand_config_path(raw: str) -> Path:
    value = str(raw or "").strip() or default_received_files_dir()
    return Path(os.path.expandvars(value)).expanduser().resolve()


def received_files_dir(cfg: Dict[str, Any]) -> Path:
    path = expand_config_path(str(cfg.get("received_files_dir", default_received_files_dir())))
    path.mkdir(parents=True, exist_ok=True)
    return path


def _is_within(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except Exception:
        return False


def is_served_file(cfg: Dict[str, Any], path: Path) -> bool:
    roots = (
        received_files_dir(cfg), OUTBOX_DIR, LEGACY_UPLOAD_DIR,
        LEGACY_APP_DIR / "outbox", LEGACY_APP_DIR / "uploads",
        legacy_received_files_dir(),
    )
    return any(_is_within(path, root) for root in roots)


def log(msg: str) -> None:
    ensure_dirs()
    stamp = _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] {msg}\n"
    try:
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass
    try:
        print(line.rstrip(), flush=True)
    except Exception:
        pass


def pin_hash(pin: str, salt: bytes) -> str:
    raw = hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), salt, PIN_ITERATIONS)
    return base64.b64encode(raw).decode("ascii")


def create_default_config() -> Dict[str, Any]:
    ensure_dirs()
    pin = f"{secrets.randbelow(1_000_000):06d}"
    salt = secrets.token_bytes(16)
    cfg = {
        "version": 4,
        "host": "0.0.0.0",
        "port": DEFAULT_PORT,
        "lan_only": True,
        "max_upload_mb": 50,
        "allowed_extensions": DEFAULT_ALLOWED_EXTENSIONS,
        "pin_salt_b64": base64.b64encode(salt).decode("ascii"),
        "pin_hash_b64": pin_hash(pin, salt),
        "session_hours": SESSION_HOURS,
        "popup_default_duration": 15,
        "pairing_ttl_seconds": 600,
        "device_name": "BASKA SEND",
        "received_files_dir": default_received_files_dir(),
        "organize_received_files": True,
        "received_file_categories": {
            "Gambar": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"],
            "PDF": [".pdf"],
            "Dokumen": [".docx", ".txt"],
            "Spreadsheet": [".xlsx", ".csv"],
            "Presentasi": [".pptx"]
        },
    }
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    FIRST_PIN_PATH.write_text(
        "BASKA SEND - PIN pertama\n"
        f"PIN: {pin}\n\n"
        "Segera ganti PIN dengan:\n"
        f'  "{sys.executable}" "{Path(__file__).resolve()}" --set-pin PIN_BARU\n',
        encoding="utf-8",
    )
    log(f"Konfigurasi baru dibuat. PIN awal: {FIRST_PIN_PATH}")
    return cfg


def save_config(cfg: Dict[str, Any]) -> None:
    ensure_dirs()
    tmp = CONFIG_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(CONFIG_PATH)


def load_config() -> Dict[str, Any]:
    ensure_dirs()
    if not CONFIG_PATH.exists():
        return create_default_config()
    try:
        cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        raise RuntimeError(f"Config rusak: {CONFIG_PATH}: {e}")
    changed = False
    defaults = {
        "version": 4,
        "host": "0.0.0.0",
        "port": DEFAULT_PORT,
        "lan_only": True,
        "max_upload_mb": 50,
        "allowed_extensions": DEFAULT_ALLOWED_EXTENSIONS,
        "session_hours": SESSION_HOURS,
        "popup_default_duration": 15,
        "pairing_ttl_seconds": 600,
        "device_name": "BASKA SEND",
        "received_files_dir": default_received_files_dir(),
        "organize_received_files": True,
        "received_file_categories": {
            "Gambar": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"],
            "PDF": [".pdf"],
            "Dokumen": [".docx", ".txt"],
            "Spreadsheet": [".xlsx", ".csv"],
            "Presentasi": [".pptx"]
        },
    }
    for k, v in defaults.items():
        if k not in cfg:
            cfg[k] = v
            changed = True

    # One-time branding migration while preserving customized values.
    if str(cfg.get("device_name", "")).strip() == LEGACY_DISPLAY_NAME:
        cfg["device_name"] = APP_TITLE
        changed = True
    raw_receive = str(cfg.get("received_files_dir", "") or "").strip()
    normalized_receive = raw_receive.replace("\\", "/").rstrip("/").lower()
    legacy_suffix = "/downloads/baska hub"
    if normalized_receive.endswith(legacy_suffix) and (
        normalized_receive.startswith("%userprofile%")
        or normalized_receive.startswith("$userprofile")
        or normalized_receive.startswith(str(Path.home()).replace("\\", "/").lower())
    ):
        cfg["received_files_dir"] = default_received_files_dir()
        changed = True
    if int(cfg.get("version", 0) or 0) < 4:
        cfg["version"] = 4
        changed = True
    if changed:
        save_config(cfg)
    return cfg


def set_pin(new_pin: str) -> None:
    if not re.fullmatch(r"\d{4,12}", new_pin):
        raise ValueError("PIN harus 4-12 digit angka.")
    cfg = load_config()
    salt = secrets.token_bytes(16)
    cfg["pin_salt_b64"] = base64.b64encode(salt).decode("ascii")
    cfg["pin_hash_b64"] = pin_hash(new_pin, salt)
    save_config(cfg)
    try:
        FIRST_PIN_PATH.unlink(missing_ok=True)
    except Exception:
        pass
    print("PIN berhasil diubah.")


def verify_pin(cfg: Dict[str, Any], pin: str) -> bool:
    try:
        salt = base64.b64decode(cfg["pin_salt_b64"])
        expected = cfg["pin_hash_b64"]
        actual = pin_hash(pin, salt)
        return hmac.compare_digest(expected, actual)
    except Exception:
        return False


def verify_main_pin_with_legacy_recovery(cfg: Dict[str, Any], pin: str) -> bool:
    """Verify the active main PIN, then recover the legacy PIN after a branding migration if needed."""
    if verify_pin(cfg, pin):
        return True
    try:
        legacy_cfg_path = LEGACY_APP_DIR / "config.json"
        if not legacy_cfg_path.exists():
            return False
        legacy_cfg = json.loads(legacy_cfg_path.read_text(encoding="utf-8"))
        if not verify_pin(legacy_cfg, pin):
            return False
        salt_b64 = legacy_cfg.get("pin_salt_b64")
        hash_b64 = legacy_cfg.get("pin_hash_b64")
        if not salt_b64 or not hash_b64:
            return False
        cfg["pin_salt_b64"] = salt_b64
        cfg["pin_hash_b64"] = hash_b64
        save_config(cfg)
        log("PIN utama dipulihkan dari konfigurasi lama PCMessageHub setelah migrasi branding.")
        return True
    except Exception as e:
        log(f"Pemulihan PIN legacy dilewati: {e}")
        return False


def now_iso() -> str:
    return _dt.datetime.now().astimezone().isoformat(timespec="seconds")


def format_datetime_id(value: Any) -> str:
    hari = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    bulan = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    try:
        if isinstance(value, _dt.datetime):
            dt = value.astimezone()
        else:
            dt = _dt.datetime.fromisoformat(str(value)).astimezone()
        return f"{hari[dt.weekday()]}, {dt.day:02d} {bulan[dt.month-1]} {dt.year} • {dt:%H:%M:%S}"
    except Exception:
        return str(value or "")


def local_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"
    finally:
        s.close()


def is_private_source(ip_text: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_text)
        return ip.is_private or ip.is_loopback or ip.is_link_local
    except ValueError:
        return False


def is_loopback_source(ip_text: str) -> bool:
    try:
        return ipaddress.ip_address(str(ip_text)).is_loopback
    except ValueError:
        return False


def local_machine_addresses() -> set:
    """Return IP addresses that belong to this PC. Used only for trusted local-browser access."""
    out = {"127.0.0.1", "::1"}
    try:
        out.add(local_ip())
    except Exception:
        pass
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None):
            addr = info[4][0]
            if addr:
                out.add(str(addr).split("%", 1)[0])
    except Exception:
        pass
    return out


def is_local_machine_source(ip_text: str) -> bool:
    raw = str(ip_text or "").split("%", 1)[0]
    if is_loopback_source(raw):
        return True
    try:
        needle = ipaddress.ip_address(raw)
    except ValueError:
        return False
    for item in local_machine_addresses():
        try:
            if needle == ipaddress.ip_address(str(item).split("%", 1)[0]):
                return True
        except ValueError:
            continue
    return False


def safe_filename(name: str) -> str:
    name = Path(name or "file").name
    name = re.sub(r"[\x00-\x1f<>:\"/\\|?*]+", "_", name)
    name = re.sub(r"\s+", " ", name).strip(" .")
    return (name or "file")[:180]


def file_allowed(cfg: Dict[str, Any], filename: str, data: bytes) -> Tuple[bool, str]:
    ext = Path(filename).suffix.lower()
    allowed = {str(x).lower() for x in cfg.get("allowed_extensions", [])}
    if ext in DANGEROUS_EXTENSIONS:
        return False, f"Tipe file berbahaya ditolak: {ext}"
    if ext not in allowed:
        return False, f"Tipe file tidak diizinkan: {ext or '(tanpa ekstensi)'}"
    if data.startswith(b"MZ") or data.startswith(b"\x7fELF"):
        return False, "Isi file terdeteksi sebagai executable dan ditolak."
    if data[:4] in {b"\xfe\xed\xfa\xce", b"\xce\xfa\xed\xfe", b"\xfe\xed\xfa\xcf", b"\xcf\xfa\xed\xfe"}:
        return False, "Isi file terdeteksi sebagai executable dan ditolak."
    if ext == ".pdf" and data and not data.startswith(b"%PDF"):
        return False, "Ekstensi PDF tidak cocok dengan isi file."
    if ext in {".docx", ".xlsx", ".pptx"}:
        if data and not data.startswith(b"PK"):
            return False, "Ekstensi dokumen tidak cocok dengan isi file."
        try:
            with zipfile.ZipFile(io.BytesIO(data), "r") as zf:
                names = {n.lower() for n in zf.namelist()}
                if "[content_types].xml" not in names:
                    return False, "Struktur Office Open XML tidak valid."
                required_prefix = {".docx": "word/", ".xlsx": "xl/", ".pptx": "ppt/"}[ext]
                if not any(n.startswith(required_prefix) for n in names):
                    return False, f"Isi file tidak cocok dengan format {ext}."
                if any(n.endswith("vbaproject.bin") for n in names):
                    return False, "Dokumen yang berisi macro VBA ditolak."
        except Exception:
            return False, "Dokumen Office rusak atau bukan format yang valid."
    if ext in {".jpg", ".jpeg"} and data and not data.startswith(b"\xff\xd8\xff"):
        return False, "Ekstensi JPEG tidak cocok dengan isi file."
    if ext == ".png" and data and not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return False, "Ekstensi PNG tidak cocok dengan isi file."
    if ext == ".gif" and data and not (data.startswith(b"GIF87a") or data.startswith(b"GIF89a")):
        return False, "Ekstensi GIF tidak cocok dengan isi file."
    if ext == ".bmp" and data and not data.startswith(b"BM"):
        return False, "Ekstensi BMP tidak cocok dengan isi file."
    if ext == ".webp" and data and not (len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP"):
        return False, "Ekstensi WEBP tidak cocok dengan isi file."
    return True, ""


def _collision_safe_path(folder: Path, filename: str) -> Path:
    safe = safe_filename(filename)
    candidate = folder / safe
    if not candidate.exists():
        return candidate
    stem, suffix = Path(safe).stem, Path(safe).suffix
    for i in range(2, 10000):
        candidate = folder / f"{stem} ({i}){suffix}"
        if not candidate.exists():
            return candidate
    return folder / f"{stem}_{uuid.uuid4().hex[:8]}{suffix}"


def received_file_category(cfg: Dict[str, Any], filename: str) -> str:
    if not bool(cfg.get("organize_received_files", True)):
        return ""
    ext = Path(filename or "").suffix.lower()
    mapping = cfg.get("received_file_categories") or {}
    if isinstance(mapping, dict):
        for category, exts in mapping.items():
            try:
                if ext in {str(x).lower() for x in (exts or [])}:
                    return safe_filename(str(category))[:40] or "Lainnya"
            except Exception:
                continue
    return "Lainnya"


def save_received_bytes(cfg: Dict[str, Any], filename: str, data: bytes) -> Tuple[str, str, int, str]:
    folder = received_files_dir(cfg)
    category = received_file_category(cfg, filename)
    if category:
        folder = folder / category
        folder.mkdir(parents=True, exist_ok=True)
    path = _collision_safe_path(folder, filename)
    path.write_bytes(data)
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return str(path), path.name, len(data), mime


def save_reply_bytes(filename: str, data: bytes) -> Tuple[str, str, int, str]:
    day_dir = OUTBOX_DIR / _dt.datetime.now().strftime("%Y%m%d")
    day_dir.mkdir(parents=True, exist_ok=True)
    safe = safe_filename(filename)
    path = day_dir / f"{uuid.uuid4().hex}_{safe}"
    path.write_bytes(data)
    mime = mimetypes.guess_type(safe)[0] or "application/octet-stream"
    return str(path), safe, len(data), mime


def save_local_reply_file(cfg: Dict[str, Any], source_path: str) -> Tuple[str, str, int, str]:
    p = Path(source_path)
    data = p.read_bytes()
    max_bytes = int(cfg.get("max_upload_mb", 50)) * 1024 * 1024
    if len(data) > max_bytes:
        raise ValueError(f"File melebihi batas {cfg.get('max_upload_mb', 50)} MB.")
    ok, why = file_allowed(cfg, p.name, data)
    if not ok:
        raise ValueError(why)
    return save_reply_bytes(p.name, data)


def db_conn() -> sqlite3.Connection:
    ensure_dirs()
    con = sqlite3.connect(DB_PATH, timeout=15)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    return con


def init_db() -> None:
    with db_conn() as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                peer_id TEXT NOT NULL,
                direction TEXT NOT NULL CHECK(direction IN ('to_pc','to_device')),
                sender TEXT NOT NULL,
                text TEXT NOT NULL DEFAULT '',
                file_path TEXT,
                file_name TEXT,
                mime TEXT,
                file_size INTEGER NOT NULL DEFAULT 0,
                notify_mode TEXT NOT NULL DEFAULT 'popup',
                duration INTEGER NOT NULL DEFAULT 15,
                allow_close INTEGER NOT NULL DEFAULT 1,
                allow_reply INTEGER NOT NULL DEFAULT 1,
                allow_copy INTEGER NOT NULL DEFAULT 1,
                sound TEXT NOT NULL DEFAULT 'default',
                created_at TEXT NOT NULL,
                desktop_delivered INTEGER NOT NULL DEFAULT 0,
                scope TEXT NOT NULL DEFAULT 'private',
                deleted INTEGER NOT NULL DEFAULT 0,
                sender_peer_id TEXT,
                target_peer_id TEXT,
                reply_to_id INTEGER,
                delivered_at TEXT,
                opened_at TEXT,
                replied_at TEXT
            )
            """
        )
        cols = {r[1] for r in con.execute("PRAGMA table_info(messages)").fetchall()}
        migrations = {
            "scope": "ALTER TABLE messages ADD COLUMN scope TEXT NOT NULL DEFAULT 'private'",
            "deleted": "ALTER TABLE messages ADD COLUMN deleted INTEGER NOT NULL DEFAULT 0",
            "sender_peer_id": "ALTER TABLE messages ADD COLUMN sender_peer_id TEXT",
            "target_peer_id": "ALTER TABLE messages ADD COLUMN target_peer_id TEXT",
            "reply_to_id": "ALTER TABLE messages ADD COLUMN reply_to_id INTEGER",
            "delivered_at": "ALTER TABLE messages ADD COLUMN delivered_at TEXT",
            "opened_at": "ALTER TABLE messages ADD COLUMN opened_at TEXT",
            "replied_at": "ALTER TABLE messages ADD COLUMN replied_at TEXT",
        }
        for col, sql in migrations.items():
            if col not in cols:
                con.execute(sql)
        # Migrate old rows to the new routing model without losing history.
        con.execute("""
            UPDATE messages
               SET sender_peer_id = CASE WHEN direction='to_pc' THEN peer_id ELSE '__pc__' END
             WHERE sender_peer_id IS NULL OR sender_peer_id=''
        """)
        con.execute("""
            UPDATE messages
               SET target_peer_id = CASE WHEN direction='to_pc' THEN '__pc__' ELSE peer_id END
             WHERE target_peer_id IS NULL OR target_peer_id=''
        """)
        con.execute("UPDATE messages SET delivered_at=created_at WHERE delivered_at IS NULL AND desktop_delivered=1")
        con.execute("CREATE INDEX IF NOT EXISTS idx_messages_peer_id ON messages(peer_id, id)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_messages_scope ON messages(scope, id)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_messages_route ON messages(sender_peer_id, target_peer_id, id)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_messages_pending ON messages(direction, desktop_delivered, id)")

        con.execute(
            """
            CREATE TABLE IF NOT EXISTS devices (
                peer_id TEXT PRIMARY KEY,
                device_name TEXT NOT NULL,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                last_ip TEXT NOT NULL DEFAULT '',
                pin_salt_b64 TEXT,
                pin_hash_b64 TEXT,
                revoked INTEGER NOT NULL DEFAULT 0,
                blocked INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        device_cols = {r[1] for r in con.execute("PRAGMA table_info(devices)").fetchall()}
        if "blocked" not in device_cols:
            con.execute("ALTER TABLE devices ADD COLUMN blocked INTEGER NOT NULL DEFAULT 0")
        con.execute("CREATE INDEX IF NOT EXISTS idx_devices_last_seen ON devices(last_seen)")
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS pairings (
                token_hash TEXT PRIMARY KEY,
                code TEXT UNIQUE NOT NULL,
                created_by_peer TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at REAL NOT NULL,
                used INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        pair_cols = {r[1] for r in con.execute("PRAGMA table_info(pairings)").fetchall()}
        if "used_at" not in pair_cols:
            con.execute("ALTER TABLE pairings ADD COLUMN used_at TEXT")
        if "used_by_peer" not in pair_cols:
            con.execute("ALTER TABLE pairings ADD COLUMN used_by_peer TEXT")
        if "canceled" not in pair_cols:
            con.execute("ALTER TABLE pairings ADD COLUMN canceled INTEGER NOT NULL DEFAULT 0")
        con.execute("CREATE INDEX IF NOT EXISTS idx_pairings_code ON pairings(code)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_pairings_expires ON pairings(expires_at,used,canceled)")



def insert_message(
    *, peer_id: str, direction: str, sender: str, text: str = "",
    file_path: Optional[str] = None, file_name: Optional[str] = None,
    mime: Optional[str] = None, file_size: int = 0,
    notify_mode: str = "popup", duration: int = 15,
    allow_close: bool = True, allow_reply: bool = True,
    allow_copy: bool = True, sound: str = "default",
    desktop_delivered: int = 0, scope: str = "private",
    sender_peer_id: Optional[str] = None, target_peer_id: Optional[str] = None,
    reply_to_id: Optional[int] = None, delivered_at: Optional[str] = None,
) -> int:
    scope = "public" if scope == "public" else "private"
    sender_peer_id = sender_peer_id or (peer_id if direction == "to_pc" else "__pc__")
    if scope == "public":
        target_peer_id = "__public__"
    else:
        target_peer_id = target_peer_id or ("__pc__" if direction == "to_pc" else peer_id)
    with db_conn() as con:
        cur = con.execute(
            """
            INSERT INTO messages
            (peer_id,direction,sender,text,file_path,file_name,mime,file_size,notify_mode,duration,
             allow_close,allow_reply,allow_copy,sound,created_at,desktop_delivered,scope,deleted,
             sender_peer_id,target_peer_id,reply_to_id,delivered_at,opened_at,replied_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0,?,?,?,?,NULL,NULL)
            """,
            (
                peer_id, direction, sender, text, file_path, file_name, mime, int(file_size or 0),
                notify_mode, int(duration), int(bool(allow_close)), int(bool(allow_reply)),
                int(bool(allow_copy)), sound, now_iso(), int(desktop_delivered), scope,
                sender_peer_id, target_peer_id, int(reply_to_id) if reply_to_id else None, delivered_at,
            ),
        )
        mid = int(cur.lastrowid)
        if reply_to_id:
            con.execute("UPDATE messages SET replied_at=COALESCE(replied_at, ?) WHERE id=?", (now_iso(), int(reply_to_id)))
        return mid


def _message_status(row: sqlite3.Row) -> str:
    keys = set(row.keys())
    if "replied_at" in keys and row["replied_at"]:
        return "replied"
    if "opened_at" in keys and row["opened_at"]:
        return "opened"
    if "delivered_at" in keys and row["delivered_at"]:
        return "delivered"
    return "sent"


def _reply_preview(reply_to_id: Optional[int]) -> Optional[Dict[str, Any]]:
    if not reply_to_id:
        return None
    with db_conn() as con:
        r = con.execute("SELECT id,sender,text,file_name,deleted FROM messages WHERE id=?", (int(reply_to_id),)).fetchone()
    if not r:
        return {"id": int(reply_to_id), "sender": "Pesan", "text": "Pesan tidak tersedia", "file_name": None, "deleted": True}
    return {
        "id": int(r["id"]), "sender": r["sender"],
        "text": ("Pesan telah dihapus" if bool(r["deleted"]) else str(r["text"] or "")[:240]),
        "file_name": r["file_name"], "deleted": bool(r["deleted"]),
    }


def row_to_public(row: sqlite3.Row) -> Dict[str, Any]:
    keys = set(row.keys())
    reply_to_id = row["reply_to_id"] if "reply_to_id" in keys else None
    return {
        "id": row["id"],
        "peer_id": row["peer_id"],
        "direction": row["direction"],
        "sender": row["sender"],
        "sender_peer_id": row["sender_peer_id"] if "sender_peer_id" in keys else (row["peer_id"] if row["direction"] == "to_pc" else "__pc__"),
        "target_peer_id": row["target_peer_id"] if "target_peer_id" in keys else ("__pc__" if row["direction"] == "to_pc" else row["peer_id"]),
        "text": row["text"],
        "file_name": row["file_name"],
        "mime": row["mime"],
        "file_size": row["file_size"],
        "notify_mode": row["notify_mode"],
        "duration": row["duration"],
        "allow_close": bool(row["allow_close"]),
        "allow_reply": bool(row["allow_reply"]),
        "allow_copy": bool(row["allow_copy"]),
        "desktop_delivered": bool(row["desktop_delivered"]),
        "scope": row["scope"] if "scope" in keys else "private",
        "deleted": bool(row["deleted"]) if "deleted" in keys else False,
        "created_at": row["created_at"],
        "reply_to_id": reply_to_id,
        "reply_preview": _reply_preview(reply_to_id),
        "delivered_at": row["delivered_at"] if "delivered_at" in keys else None,
        "opened_at": row["opened_at"] if "opened_at" in keys else None,
        "replied_at": row["replied_at"] if "replied_at" in keys else None,
        "status": _message_status(row),
    }


def get_message(message_id: int) -> Optional[sqlite3.Row]:
    with db_conn() as con:
        return con.execute("SELECT * FROM messages WHERE id=?", (int(message_id),)).fetchone()


def get_messages(peer_id: str, room: str = "private", after: int = 0, limit: int = 200, partner_peer: Optional[str] = None):
    limit = max(1, min(int(limit), 500))
    room = "public" if room == "public" else "private"
    with db_conn() as con:
        if room == "public":
            rows = con.execute(
                "SELECT * FROM messages WHERE scope='public' AND deleted=0 AND id>? ORDER BY id ASC LIMIT ?",
                (int(after), limit),
            ).fetchall()
        elif partner_peer:
            partner_peer = str(partner_peer)[:64]
            rows = con.execute(
                """SELECT * FROM messages
                   WHERE scope='private' AND deleted=0 AND id>?
                     AND ((sender_peer_id=? AND target_peer_id=?) OR (sender_peer_id=? AND target_peer_id=?))
                   ORDER BY id ASC LIMIT ?""",
                (int(after), peer_id, partner_peer, partner_peer, peer_id, limit),
            ).fetchall()
        else:
            rows = con.execute(
                """SELECT * FROM messages
                   WHERE scope='private' AND deleted=0 AND id>?
                     AND (sender_peer_id=? OR target_peer_id=?)
                   ORDER BY id ASC LIMIT ?""",
                (int(after), peer_id, peer_id, limit),
            ).fetchall()
    return [row_to_public(r) for r in rows]


def get_message_updates(peer_id: str, room: str = "private", limit: int = 300, partner_peer: Optional[str] = None) -> Dict[str, Any]:
    room = "public" if room == "public" else "private"
    with db_conn() as con:
        if room == "public":
            rows = con.execute(
                "SELECT id,deleted,delivered_at,opened_at,replied_at FROM messages WHERE scope='public' ORDER BY id DESC LIMIT ?",
                (int(limit),),
            ).fetchall()
        elif partner_peer:
            rows = con.execute(
                """SELECT id,deleted,delivered_at,opened_at,replied_at FROM messages
                   WHERE scope='private'
                     AND ((sender_peer_id=? AND target_peer_id=?) OR (sender_peer_id=? AND target_peer_id=?))
                   ORDER BY id DESC LIMIT ?""",
                (peer_id, partner_peer, partner_peer, peer_id, int(limit)),
            ).fetchall()
        else:
            rows = con.execute(
                """SELECT id,deleted,delivered_at,opened_at,replied_at FROM messages
                   WHERE scope='private' AND (sender_peer_id=? OR target_peer_id=?)
                   ORDER BY id DESC LIMIT ?""",
                (peer_id, peer_id, int(limit)),
            ).fetchall()
    out = []
    for r in rows:
        status = "replied" if r["replied_at"] else "opened" if r["opened_at"] else "delivered" if r["delivered_at"] else "sent"
        out.append({"id": int(r["id"]), "deleted": bool(r["deleted"]), "status": status})
    return {"updates": out}


def soft_delete_message(message_id: int) -> None:
    with db_conn() as con:
        con.execute("UPDATE messages SET deleted=1 WHERE id=?", (int(message_id),))


def pending_desktop_messages(limit: int = 100):
    with db_conn() as con:
        return con.execute(
            """SELECT * FROM messages
               WHERE sender_peer_id!='__pc__' AND desktop_delivered=0 AND deleted=0
                 AND (target_peer_id='__pc__' OR scope='public')
               ORDER BY id ASC LIMIT ?""",
            (limit,),
        ).fetchall()


def mark_desktop_delivered(message_id: int) -> None:
    with db_conn() as con:
        con.execute("UPDATE messages SET desktop_delivered=1, delivered_at=COALESCE(delivered_at, ?) WHERE id=?", (now_iso(), int(message_id)))


def mark_message_opened(message_id: int) -> None:
    with db_conn() as con:
        con.execute("UPDATE messages SET delivered_at=COALESCE(delivered_at, ?), opened_at=COALESCE(opened_at, ?) WHERE id=?", (now_iso(), now_iso(), int(message_id)))


def acknowledge_message(peer_id: str, message_id: int, stage: str = "opened") -> bool:
    with db_conn() as con:
        row = con.execute("SELECT * FROM messages WHERE id=?", (int(message_id),)).fetchone()
        if not row or bool(row["deleted"]):
            return False
        if row["scope"] != "public" and row["target_peer_id"] != peer_id:
            return False
        now = now_iso()
        if stage == "opened":
            con.execute("UPDATE messages SET delivered_at=COALESCE(delivered_at, ?), opened_at=COALESCE(opened_at, ?) WHERE id=?", (now, now, int(message_id)))
        else:
            con.execute("UPDATE messages SET delivered_at=COALESCE(delivered_at, ?) WHERE id=?", (now, int(message_id)))
        return True


def upsert_device(peer_id: str, device_name: str, ip: str, allow_unrevoke: bool = False) -> None:
    now = now_iso()
    with db_conn() as con:
        row = con.execute("SELECT peer_id FROM devices WHERE peer_id=?", (peer_id,)).fetchone()
        if row:
            if allow_unrevoke:
                con.execute("UPDATE devices SET device_name=?,last_seen=?,last_ip=?,revoked=0 WHERE peer_id=?", (device_name, now, ip, peer_id))
            else:
                con.execute("UPDATE devices SET device_name=?,last_seen=?,last_ip=? WHERE peer_id=?", (device_name, now, ip, peer_id))
        else:
            con.execute("INSERT INTO devices(peer_id,device_name,first_seen,last_seen,last_ip,revoked,blocked) VALUES(?,?,?,?,?,0,0)", (peer_id, device_name, now, now, ip))


def touch_device(peer_id: str, device_name: str, ip: str) -> None:
    with db_conn() as con:
        con.execute("UPDATE devices SET device_name=?,last_seen=?,last_ip=? WHERE peer_id=? AND revoked=0 AND blocked=0", (device_name, now_iso(), ip, peer_id))


def get_device(peer_id: str) -> Optional[sqlite3.Row]:
    with db_conn() as con:
        return con.execute("SELECT * FROM devices WHERE peer_id=?", (peer_id,)).fetchone()


def list_devices(current_peer: str, include_revoked: bool = False) -> list:
    with db_conn() as con:
        if include_revoked:
            rows = con.execute("SELECT * FROM devices ORDER BY blocked ASC,revoked ASC,last_seen DESC").fetchall()
        else:
            rows = con.execute("SELECT * FROM devices WHERE revoked=0 AND blocked=0 ORDER BY last_seen DESC").fetchall()
    now = _dt.datetime.now().astimezone()
    result = []
    for r in rows:
        try:
            seen = _dt.datetime.fromisoformat(r["last_seen"]).astimezone()
            online = (now - seen).total_seconds() <= 45
        except Exception:
            online = False
        result.append({
            "peer_id": r["peer_id"], "device_name": r["device_name"], "last_ip": r["last_ip"],
            "first_seen": r["first_seen"], "last_seen": r["last_seen"], "online": online,
            "is_current": r["peer_id"] == current_peer, "has_pin": bool(r["pin_hash_b64"]),
            "revoked": bool(r["revoked"]), "blocked": bool(r["blocked"]) if "blocked" in set(r.keys()) else False,
        })
    return result


def unread_counts(peer_id: str) -> Dict[str, int]:
    with db_conn() as con:
        rows = con.execute(
            """SELECT sender_peer_id, COUNT(*) AS n FROM messages
               WHERE scope='private' AND target_peer_id=? AND deleted=0 AND opened_at IS NULL
               GROUP BY sender_peer_id""",
            (peer_id,),
        ).fetchall()
    return {str(r["sender_peer_id"]): int(r["n"]) for r in rows if r["sender_peer_id"]}


def set_device_pin(peer_id: str, pin: str) -> None:
    if not re.fullmatch(r"\d{4,12}", pin or ""):
        raise ValueError("PIN perangkat harus 4-12 digit angka.")
    salt = secrets.token_bytes(16)
    with db_conn() as con:
        con.execute("UPDATE devices SET pin_salt_b64=?,pin_hash_b64=? WHERE peer_id=? AND revoked=0", (
            base64.b64encode(salt).decode("ascii"), pin_hash(pin, salt), peer_id,
        ))


def verify_device_pin(peer_id: str, pin: str) -> bool:
    row = get_device(peer_id)
    if not row or bool(row["revoked"]) or ("blocked" in set(row.keys()) and bool(row["blocked"])) or not row["pin_hash_b64"] or not row["pin_salt_b64"]:
        return False
    try:
        salt = base64.b64decode(row["pin_salt_b64"])
        return hmac.compare_digest(str(row["pin_hash_b64"]), pin_hash(pin, salt))
    except Exception:
        return False


def revoke_device(peer_id: str) -> None:
    with db_conn() as con:
        con.execute("UPDATE devices SET revoked=1 WHERE peer_id=?", (peer_id,))


def restore_device(peer_id: str) -> None:
    with db_conn() as con:
        con.execute("UPDATE devices SET revoked=0 WHERE peer_id=?", (peer_id,))


def block_device(peer_id: str) -> None:
    with db_conn() as con:
        con.execute("UPDATE devices SET blocked=1 WHERE peer_id=?", (peer_id,))


def unblock_device(peer_id: str) -> None:
    with db_conn() as con:
        con.execute("UPDATE devices SET blocked=0 WHERE peer_id=?", (peer_id,))


def reset_device_pin(peer_id: str) -> None:
    with db_conn() as con:
        con.execute("UPDATE devices SET pin_salt_b64=NULL,pin_hash_b64=NULL WHERE peer_id=?", (peer_id,))


def delete_registered_device(peer_id: str) -> None:
    with db_conn() as con:
        con.execute("UPDATE pairings SET canceled=1 WHERE created_by_peer=? AND used=0", (peer_id,))
        con.execute("DELETE FROM devices WHERE peer_id=?", (peer_id,))


def clear_room_messages(peer_id: str, room: str, partner_peer: Optional[str], *, clear_public_all: bool = False) -> list:
    """Remove chat history from the server, not merely from the browser DOM.

    Private: clears the entire selected two-party conversation.
    Public: a normal device removes only its own public messages; a localhost admin
    may clear the whole public room. Files already saved on disk are intentionally kept.
    """
    room = "public" if room == "public" else "private"
    with db_conn() as con:
        if room == "public":
            if clear_public_all:
                rows = con.execute("SELECT id FROM messages WHERE scope='public'").fetchall()
                con.execute("DELETE FROM messages WHERE scope='public'")
            else:
                rows = con.execute("SELECT id FROM messages WHERE scope='public' AND sender_peer_id=?", (peer_id,)).fetchall()
                con.execute("DELETE FROM messages WHERE scope='public' AND sender_peer_id=?", (peer_id,))
        else:
            partner = str(partner_peer or "__pc__")[:64]
            rows = con.execute(
                """SELECT id FROM messages WHERE scope='private'
                   AND ((sender_peer_id=? AND target_peer_id=?) OR (sender_peer_id=? AND target_peer_id=?))""",
                (peer_id, partner, partner, peer_id),
            ).fetchall()
            con.execute(
                """DELETE FROM messages WHERE scope='private'
                   AND ((sender_peer_id=? AND target_peer_id=?) OR (sender_peer_id=? AND target_peer_id=?))""",
                (peer_id, partner, partner, peer_id),
            )
    return [int(r["id"]) for r in rows]


def _normalize_pairing_value(value: str) -> str:
    value = str(value or "").strip()
    if re.fullmatch(r"[\d\s-]+", value):
        digits = re.sub(r"\D", "", value)
        if len(digits) == 6:
            return digits
    return value


def _pairing_row(value: str) -> Optional[sqlite3.Row]:
    value = _normalize_pairing_value(value)
    if not value:
        return None
    with db_conn() as con:
        if re.fullmatch(r"\d{6}", value):
            return con.execute(
                "SELECT * FROM pairings WHERE code=? ORDER BY expires_at DESC LIMIT 1",
                (value,),
            ).fetchone()
        token_hash = hashlib.sha256(value.encode("utf-8")).hexdigest()
        return con.execute("SELECT * FROM pairings WHERE token_hash=? LIMIT 1", (token_hash,)).fetchone()


def inspect_pairing(value: str) -> Dict[str, Any]:
    row = _pairing_row(value)
    if not row:
        return {"ok": False, "status": "invalid", "expires_at": None, "expires_in": 0}
    keys = set(row.keys())
    now = time.time()
    if "canceled" in keys and bool(row["canceled"]):
        status = "canceled"
    elif bool(row["used"]):
        status = "used"
    elif float(row["expires_at"]) <= now:
        status = "expired"
    else:
        status = "valid"
    return {
        "ok": status == "valid",
        "status": status,
        "expires_at": float(row["expires_at"]),
        "expires_in": max(0, int(float(row["expires_at"]) - now)),
        "code": str(row["code"]),
    }


def pairing_status_message(status: str) -> str:
    return {
        "invalid": "Kode/tautan pairing tidak ditemukan. Buat pairing baru dari menu Perangkat di BASKA SEND.",
        "used": "Kode/tautan pairing sudah pernah dipakai. Buat kode pairing baru.",
        "expired": "Kode/tautan pairing sudah kedaluwarsa. Buat pairing baru lalu gunakan sebelum countdown habis.",
        "canceled": "Kode/tautan pairing sudah dibatalkan atau diganti oleh kode yang lebih baru.",
    }.get(str(status), "Pairing tidak dapat digunakan.")


def create_pairing(created_by_peer: str, ttl_seconds: int = 600) -> Dict[str, Any]:
    ttl_seconds = max(120, min(int(ttl_seconds), 1800))
    token = secrets.token_urlsafe(24)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    expires = time.time() + ttl_seconds
    code = ""
    with db_conn() as con:
        # Keep a single active code per admin session to avoid users accidentally using an old code.
        con.execute(
            "UPDATE pairings SET canceled=1 WHERE created_by_peer=? AND used=0 AND canceled=0 AND expires_at>?",
            (created_by_peer, time.time()),
        )
        for _ in range(40):
            candidate = f"{secrets.randbelow(1_000_000):06d}"
            if not con.execute(
                "SELECT 1 FROM pairings WHERE code=? AND used=0 AND canceled=0 AND expires_at>?",
                (candidate, time.time()),
            ).fetchone():
                code = candidate
                break
        if not code:
            raise RuntimeError("Tidak dapat membuat kode pairing unik.")
        con.execute("DELETE FROM pairings WHERE expires_at<? AND (used=1 OR canceled=1)", (time.time() - 86400,))
        con.execute(
            "INSERT INTO pairings(token_hash,code,created_by_peer,created_at,expires_at,used,used_at,used_by_peer,canceled) VALUES(?,?,?,?,?,0,NULL,NULL,0)",
            (token_hash, code, created_by_peer, now_iso(), expires),
        )
    return {"token": token, "code": code, "expires_at": expires, "expires_in": ttl_seconds}


def cancel_active_pairing(created_by_peer: str) -> int:
    with db_conn() as con:
        cur = con.execute(
            "UPDATE pairings SET canceled=1 WHERE created_by_peer=? AND used=0 AND canceled=0 AND expires_at>?",
            (created_by_peer, time.time()),
        )
        return int(cur.rowcount or 0)


def consume_pairing(value: str, used_by_peer: str = "") -> Dict[str, Any]:
    value = _normalize_pairing_value(value)
    if not value:
        return {"ok": False, "status": "invalid"}
    con = db_conn()
    try:
        con.execute("BEGIN IMMEDIATE")
        if re.fullmatch(r"\d{6}", value):
            row = con.execute(
                "SELECT * FROM pairings WHERE code=? ORDER BY expires_at DESC LIMIT 1",
                (value,),
            ).fetchone()
        else:
            token_hash = hashlib.sha256(value.encode("utf-8")).hexdigest()
            row = con.execute("SELECT * FROM pairings WHERE token_hash=? LIMIT 1", (token_hash,)).fetchone()
        if not row:
            con.commit()
            return {"ok": False, "status": "invalid"}
        keys = set(row.keys())
        now = time.time()
        if "canceled" in keys and bool(row["canceled"]):
            con.commit(); return {"ok": False, "status": "canceled"}
        if bool(row["used"]):
            con.commit(); return {"ok": False, "status": "used"}
        if float(row["expires_at"]) <= now:
            con.commit(); return {"ok": False, "status": "expired"}
        cur = con.execute(
            "UPDATE pairings SET used=1, used_at=?, used_by_peer=? WHERE token_hash=? AND used=0 AND canceled=0 AND expires_at>?",
            (now_iso(), str(used_by_peer or "")[:64], row["token_hash"], now),
        )
        if int(cur.rowcount or 0) != 1:
            con.commit(); return {"ok": False, "status": "used"}
        con.commit()
        return {"ok": True, "status": "accepted", "code": str(row["code"]), "expires_at": float(row["expires_at"])}
    except Exception:
        try:
            con.rollback()
        except Exception:
            pass
        raise
    finally:
        con.close()


@dataclass
class Session:
    token: str
    csrf: str
    peer_id: str
    device_name: str
    expires_at: float
    is_admin: bool = False
    auth_mode: str = "device"


class SessionStore:
    def __init__(self, hours: int):
        self.hours = hours
        self._lock = threading.Lock()
        self._items: Dict[str, Session] = {}

    def create(self, peer_id: str, device_name: str, *, is_admin: bool = False, auth_mode: str = "device") -> Session:
        s = Session(
            token=secrets.token_urlsafe(32),
            csrf=secrets.token_urlsafe(24),
            peer_id=peer_id,
            device_name=device_name,
            expires_at=time.time() + self.hours * 3600,
            is_admin=bool(is_admin),
            auth_mode=str(auth_mode or "device"),
        )
        with self._lock:
            self._items[s.token] = s
        return s

    def get(self, token: str) -> Optional[Session]:
        if not token:
            return None
        with self._lock:
            s = self._items.get(token)
            if not s:
                return None
            if s.expires_at < time.time():
                self._items.pop(token, None)
                return None
            row = get_device(s.peer_id)
            if row is not None:
                keys = set(row.keys())
                if bool(row["revoked"]) or ("blocked" in keys and bool(row["blocked"])):
                    self._items.pop(token, None)
                    return None
            return s

    def delete(self, token: str) -> None:
        with self._lock:
            self._items.pop(token, None)

    def delete_peer(self, peer_id: str) -> None:
        with self._lock:
            for token in [t for t, s in self._items.items() if s.peer_id == peer_id]:
                self._items.pop(token, None)


class LoginGuard:
    def __init__(self):
        self._lock = threading.Lock()
        self._failures: Dict[str, list] = {}
        self._locked_until: Dict[str, float] = {}

    def is_locked(self, ip: str) -> int:
        with self._lock:
            until = self._locked_until.get(ip, 0)
            if until > time.time():
                return max(1, int(until - time.time()))
            self._locked_until.pop(ip, None)
            return 0

    def failed(self, ip: str) -> None:
        now = time.time()
        with self._lock:
            arr = [t for t in self._failures.get(ip, []) if now - t < 60]
            arr.append(now)
            self._failures[ip] = arr
            if len(arr) >= 5:
                self._locked_until[ip] = now + 300
                self._failures[ip] = []

    def success(self, ip: str) -> None:
        with self._lock:
            self._failures.pop(ip, None)
            self._locked_until.pop(ip, None)

def _rs_multiply(x: int, y: int) -> int:
    z = 0
    for i in range(7, -1, -1):
        z = (z << 1) ^ ((z >> 7) * 0x11D)
        z ^= ((y >> i) & 1) * x
    return z & 0xFF


def _rs_divisor(degree: int) -> bytes:
    result = bytearray([0] * (degree - 1) + [1])
    root = 1
    for _ in range(degree):
        for j in range(degree):
            result[j] = _rs_multiply(result[j], root)
            if j + 1 < degree:
                result[j] ^= result[j + 1]
        root = _rs_multiply(root, 0x02)
    return bytes(result)


def _rs_remainder(data: bytes, divisor: bytes) -> bytes:
    result = bytearray(len(divisor))
    for b in data:
        factor = b ^ result[0]
        result[:-1] = result[1:]
        result[-1] = 0
        for i, coef in enumerate(divisor):
            result[i] ^= _rs_multiply(coef, factor)
    return bytes(result)


def qr_svg_v5_l(text: str, border: int = 4, scale: int = 5) -> str:
    """Dependency-free QR Code Model 2, fixed Version 5 / ECC-L / mask 0.

    Capacity is intentionally limited; pairing URLs are kept short enough for this version.
    Returns an SVG string suitable for direct embedding in the local WebApp.
    """
    data = text.encode("utf-8")
    data_codewords = 108  # QR v5-L
    ecc_codewords = 26
    capacity_bits = data_codewords * 8
    if len(data) > 106:
        raise ValueError("Data QR terlalu panjang.")
    bits = []

    def append_bits(value: int, count: int) -> None:
        for i in range(count - 1, -1, -1):
            bits.append((value >> i) & 1)

    append_bits(0b0100, 4)  # byte mode
    append_bits(len(data), 8)
    for b in data:
        append_bits(b, 8)
    for _ in range(min(4, capacity_bits - len(bits))):
        bits.append(0)
    while len(bits) % 8:
        bits.append(0)
    code = bytearray()
    for i in range(0, len(bits), 8):
        v = 0
        for bit in bits[i:i + 8]:
            v = (v << 1) | bit
        code.append(v)
    pad = (0xEC, 0x11)
    k = 0
    while len(code) < data_codewords:
        code.append(pad[k & 1])
        k += 1
    codewords = bytes(code) + _rs_remainder(bytes(code), _rs_divisor(ecc_codewords))

    size = 37
    modules = [[False] * size for _ in range(size)]
    function = [[False] * size for _ in range(size)]

    def setfunc(x: int, y: int, black: bool) -> None:
        if 0 <= x < size and 0 <= y < size:
            modules[y][x] = bool(black)
            function[y][x] = True

    # Timing patterns first; finder patterns overwrite the ends.
    for i in range(size):
        setfunc(6, i, i % 2 == 0)
        setfunc(i, 6, i % 2 == 0)

    def finder(cx: int, cy: int) -> None:
        for dy in range(-4, 5):
            for dx in range(-4, 5):
                x, y = cx + dx, cy + dy
                if 0 <= x < size and 0 <= y < size:
                    dist = max(abs(dx), abs(dy))
                    setfunc(x, y, dist != 2 and dist != 4)

    finder(3, 3)
    finder(size - 4, 3)
    finder(3, size - 4)

    # Version 5 alignment centres are 6 and 30; only (30,30) does not overlap a finder.
    for cy in (6, 30):
        for cx in (6, 30):
            if (cx == 6 and cy == 6) or (cx == 6 and cy == 30) or (cx == 30 and cy == 6):
                continue
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    setfunc(cx + dx, cy + dy, max(abs(dx), abs(dy)) != 1)

    # Format bits: ECC level L (01) + mask 0 (000).
    fmt_data = (1 << 3) | 0
    rem = fmt_data
    for _ in range(10):
        rem = (rem << 1) ^ ((rem >> 9) * 0x537)
    fmt = ((fmt_data << 10) | rem) ^ 0x5412

    def bit(i: int) -> bool:
        return ((fmt >> i) & 1) != 0

    for i in range(6):
        setfunc(8, i, bit(i))
    setfunc(8, 7, bit(6))
    setfunc(8, 8, bit(7))
    setfunc(7, 8, bit(8))
    for i in range(9, 15):
        setfunc(14 - i, 8, bit(i))
    for i in range(8):
        setfunc(size - 1 - i, 8, bit(i))
    for i in range(8, 15):
        setfunc(8, size - 15 + i, bit(i))
    setfunc(8, size - 8, True)  # fixed dark module

    # Data modules, zig-zag, using mask pattern 0.
    total_bits = len(codewords) * 8
    bit_index = 0
    right = size - 1
    while right >= 1:
        if right == 6:
            right = 5
        for vert in range(size):
            upward = ((right + 1) & 2) == 0
            y = size - 1 - vert if upward else vert
            for j in range(2):
                x = right - j
                if function[y][x]:
                    continue
                raw = False
                if bit_index < total_bits:
                    raw = ((codewords[bit_index >> 3] >> (7 - (bit_index & 7))) & 1) != 0
                bit_index += 1
                modules[y][x] = raw ^ ((x + y) % 2 == 0)
        right -= 2

    dim = (size + border * 2) * scale
    rects = []
    for y in range(size):
        for x in range(size):
            if modules[y][x]:
                rects.append(f'<rect x="{(x + border) * scale}" y="{(y + border) * scale}" width="{scale}" height="{scale}"/>')
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {dim} {dim}" width="{dim}" height="{dim}" '
        f'shape-rendering="crispEdges"><rect width="100%" height="100%" fill="white"/>'
        f'<g fill="black">{"".join(rects)}</g></svg>'
    )


WEB_APP = r'''<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta id="themeMeta" name="theme-color" content="#0b1020">
<title>BASKA SEND</title>
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="64x64" href="/favicon.png">
<link rel="apple-touch-icon" href="/favicon.png">
<link rel="manifest" href="/manifest.webmanifest">
<meta name="application-name" content="BASKA SEND">
<meta name="apple-mobile-web-app-title" content="BASKA SEND">
<style>
:root{--bg:#090d14;--panel:#111722;--panel2:#171f2d;--panel3:#1d2636;--line:#293445;--text:#f4f7fb;--muted:#95a1b4;--acc:#4c7dff;--acc2:#7158e8;--danger:#e24c70;--ok:#25c26e;--warn:#e5a93d;--shadow:0 24px 70px rgba(0,0,0,.34);--glass:rgba(17,23,34,.96)}
html[data-theme="light"]{--bg:#f3f6fb;--panel:#fff;--panel2:#f7f9fc;--panel3:#eef3f9;--line:#dbe3ef;--text:#172033;--muted:#667085;--acc:#245fd6;--acc2:#6d45d8;--danger:#c9365e;--ok:#169b56;--warn:#b7791f;--shadow:0 22px 60px rgba(31,41,55,.12);--glass:rgba(255,255,255,.98)}
*{box-sizing:border-box}html{color-scheme:dark}html[data-theme="light"]{color-scheme:light}html,body{margin:0;width:100%;min-height:100%;font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Arial;color:var(--text);background:var(--bg)}body{overflow:hidden}button,input,textarea,select{font:inherit}button{cursor:pointer}.hidden{display:none!important}
body:before{content:"";position:fixed;inset:0;pointer-events:none;background:radial-gradient(850px 520px at 88% -8%,rgba(76,125,255,.18),transparent 60%),radial-gradient(720px 460px at -12% 24%,rgba(113,88,232,.11),transparent 60%)}
.wrap{position:relative;z-index:1;width:100%;min-height:100vh;min-height:100dvh;display:grid;place-items:center;padding:16px}.login{width:min(440px,calc(100vw - 28px));padding:30px;border-radius:22px;background:var(--glass);border:1px solid var(--line);box-shadow:var(--shadow)}
.brandline,.brand,.top,.top-actions,.roombar,.room-tabs,.msg-actions,.modal-actions,.device-line,.composer-head{display:flex;align-items:center}.brandline,.top,.device-line,.composer-head{justify-content:space-between}.brandline{gap:14px;margin-bottom:24px}.brand{gap:11px;min-width:0}.mark{width:42px;height:42px;display:grid;place-items:center;flex:0 0 auto}.mark svg{width:40px;height:40px}.mark .m-bg{fill:var(--acc)}.mark .m-line{fill:none;stroke:#fff;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round}.brandtext{min-width:0}.title{font-weight:800;letter-spacing:-.2px}.subtitle{margin-top:3px;color:var(--muted);font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}h1{font-size:22px;margin:0;letter-spacing:-.35px}.sub{color:var(--muted);font-size:13px;margin-top:5px;line-height:1.55}
.iconbtn{width:40px;height:40px;border-radius:11px;border:1px solid var(--line);background:var(--panel2);color:var(--text);display:grid;place-items:center;flex:0 0 auto}.fieldlabel{display:block;color:var(--muted);font-size:12px;margin:16px 0 7px}.field{width:100%;border:1px solid var(--line);background:var(--panel2);color:var(--text);border-radius:12px;padding:12px 13px;outline:none;transition:.18s}.field:focus{border-color:var(--acc);box-shadow:0 0 0 3px rgba(76,125,255,.12)}
.primary{border:0;color:#fff;background:linear-gradient(135deg,var(--acc),var(--acc2));padding:12px 16px;border-radius:12px;font-weight:700}.primary.danger{background:var(--danger)}.primary:disabled{opacity:.55;cursor:not-allowed}.wide{width:100%;margin-top:18px}.error{min-height:20px;color:#ff8199;font-size:12px;margin-top:10px}.pair-note{margin:14px 0 0;padding:10px 12px;border:1px solid rgba(76,125,255,.35);background:rgba(76,125,255,.08);border-radius:12px;font-size:12px;color:var(--muted)}.pair-row{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:8px;margin-top:9px}.divider{display:flex;align-items:center;gap:10px;color:var(--muted);font-size:11px;margin-top:15px}.divider:before,.divider:after{content:"";height:1px;background:var(--line);flex:1}
.card{position:relative;width:min(1220px,100%);height:calc(100vh - 32px);height:calc(100dvh - 32px);max-height:920px;display:grid;grid-template-rows:auto auto minmax(0,1fr) auto;background:var(--glass);border:1px solid var(--line);box-shadow:var(--shadow);border-radius:22px;overflow:hidden}.top{min-height:68px;padding:10px 16px;gap:12px;border-bottom:1px solid var(--line);background:var(--panel)}.status{font-size:12px;color:var(--muted);display:flex;align-items:center;gap:7px}.dot{width:8px;height:8px;border-radius:50%;background:var(--ok);box-shadow:0 0 0 4px rgba(37,194,110,.12)}.top-actions{gap:7px;flex:0 0 auto}.ghost{border:1px solid var(--line);color:var(--text);background:var(--panel2);padding:8px 10px;border-radius:10px;white-space:nowrap}.roombar{justify-content:space-between;gap:12px;padding:8px 14px;border-bottom:1px solid var(--line);background:var(--panel)}.room-tabs{gap:7px}.room-btn{border:1px solid transparent;background:transparent;color:var(--muted);border-radius:10px;padding:8px 11px;font-weight:650}.room-btn.active{color:var(--text);background:var(--panel2);border-color:var(--line)}.room-right{display:flex;align-items:center;gap:8px;min-width:0}.room-note{font-size:11px;color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.target-select{max-width:230px;border:1px solid var(--line);background:var(--panel2);color:var(--text);border-radius:9px;padding:7px 9px;font-size:12px}
.messages{min-height:0;padding:13px 15px;overflow:auto;overscroll-behavior:contain;scroll-behavior:smooth}.empty{height:100%;display:grid;place-items:center;color:var(--muted);text-align:center;padding:24px}.empty strong{display:block;color:var(--text);font-size:16px;margin-bottom:6px}.row{display:flex;margin:5px 0}.row.mine{justify-content:flex-end}.bubble{max-width:min(720px,88%);padding:8px 10px;border:1px solid var(--line);background:var(--panel2);border-radius:14px 14px 14px 4px;box-shadow:0 5px 16px rgba(0,0,0,.08)}.mine .bubble{background:linear-gradient(135deg,var(--acc),var(--acc2));border-color:transparent;border-radius:14px 14px 4px 14px;color:#fff}.who{font-size:9.5px;color:var(--muted);margin-bottom:3px}.mine .who,.mine .meta{color:rgba(255,255,255,.78)}.txt{white-space:pre-wrap;word-break:break-word;line-height:1.32;font-size:12px}.meta{font-size:9px;color:var(--muted);margin-top:4px;text-align:right}.delivery{font-weight:650}.quote{margin:0 0 5px;padding:5px 7px;border-left:3px solid var(--acc);background:rgba(0,0,0,.10);border-radius:7px;font-size:10px;cursor:pointer}.mine .quote{border-left-color:#fff;background:rgba(0,0,0,.13)}.quote b{display:block;margin-bottom:2px}.quote span{opacity:.78;display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:520px}.file{margin-top:6px;display:flex;gap:8px;align-items:center;padding:7px;border-radius:12px;background:rgba(0,0,0,.10);text-decoration:none;color:inherit;border:1px solid rgba(255,255,255,.10)}.fi{width:34px;height:34px;border-radius:9px;background:rgba(255,255,255,.12);display:grid;place-items:center;font-size:9px;font-weight:800}.file small{display:block;opacity:.72;margin-top:2px}.preview{display:block;max-width:min(350px,100%);max-height:260px;border-radius:11px;margin-top:9px;border:1px solid rgba(255,255,255,.10);object-fit:contain}.msg-actions{justify-content:flex-end;gap:5px;margin-top:6px;flex-wrap:wrap}.mini{border:1px solid rgba(255,255,255,.22);background:rgba(255,255,255,.13);color:inherit;border-radius:8px;padding:4px 7px;font-size:10px}.mini.danger-mini{border-color:rgba(255,125,145,.38)}.mini:disabled{opacity:.65;cursor:default}
.composer{border-top:1px solid var(--line);background:var(--panel);padding:10px 13px max(10px,env(safe-area-inset-bottom));max-height:54vh;max-height:54dvh;overflow:auto}.reply-chip,.file-chip{display:none;align-items:center;gap:8px;margin-bottom:8px;padding:8px 10px;background:var(--panel2);border:1px solid var(--line);border-radius:11px;font-size:12px}.reply-chip.on,.file-chip.on{display:flex}.chip-main{min-width:0;flex:1}.chip-main b{display:block;font-size:11px}.chip-main span{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--muted);margin-top:2px}.x{border:0;background:transparent;color:#ff8199;font-size:18px}.compose-row{display:grid;grid-template-columns:auto minmax(0,1fr) auto;gap:9px;align-items:end}.attach{width:44px;height:44px;border:1px solid var(--line);border-radius:12px;background:var(--panel2);color:var(--text);font-size:20px}.textarea{resize:none;min-height:44px;max-height:120px;padding:11px 12px}.send{height:44px;min-width:92px}.settings-summary{margin-top:9px;color:var(--muted);font-size:11px;cursor:pointer;user-select:none}.settings-summary::-webkit-details-marker{display:none}.settings-summary:before{content:"⚙ ";}.message-settings[open] .settings-summary{margin-bottom:8px}.options{display:grid;grid-template-columns:1fr 1.35fr .9fr .9fr 1fr 1fr 1fr;gap:8px}.opt{min-width:0;background:var(--panel2);border:1px solid var(--line);border-radius:11px;padding:8px}.opt span{display:block;color:var(--muted);font-size:10px;margin-bottom:5px}.opt select{width:100%;min-width:0;background:transparent;color:var(--text);border:0;outline:0;font-size:12px}.tog{display:flex;align-items:center;gap:7px;height:100%;font-size:12px;color:var(--text);margin:0}.tog input{accent-color:var(--acc)}.opt.disabled{opacity:.45;pointer-events:none}.hint{font-size:10px;color:var(--muted);margin-top:8px;display:flex;justify-content:space-between;gap:10px}.hint span{min-width:0;overflow-wrap:anywhere}.progress{height:2px;margin-top:8px;background:var(--line);overflow:hidden;border-radius:2px}.progress i{display:block;height:100%;width:0;background:linear-gradient(90deg,var(--acc),var(--acc2));transition:.15s}.drop-overlay{position:absolute;z-index:20;inset:10px;display:none;place-items:center;border:2px dashed var(--acc);background:rgba(36,95,214,.10);backdrop-filter:blur(5px);border-radius:18px;color:var(--text);font-weight:750}.card.dragging .drop-overlay{display:grid}
.modal-backdrop{position:fixed;z-index:50;inset:0;background:rgba(0,0,0,.52);display:grid;place-items:center;padding:18px;backdrop-filter:blur(7px)}.modal{width:min(460px,100%);max-height:min(760px,92dvh);overflow:auto;background:var(--panel);border:1px solid var(--line);border-radius:20px;padding:20px;box-shadow:var(--shadow)}.modal.wide-modal{width:min(720px,100%)}.modal h3{margin:0 0 7px;font-size:18px}.modal p{margin:0;color:var(--muted);font-size:13px;line-height:1.55;white-space:pre-wrap}.modal-actions{justify-content:flex-end;gap:8px;margin-top:20px}.modal-actions .ghost,.modal-actions .primary{min-width:92px}.modal-input{margin-top:14px}.devices-head{display:flex;justify-content:space-between;align-items:center;gap:10px;margin-bottom:12px}.devices-actions{display:flex;gap:7px;flex-wrap:wrap}.device-list{display:grid;gap:8px}.device-item{border:1px solid var(--line);background:var(--panel2);border-radius:14px;padding:11px}.device-line{gap:10px}.device-name{font-weight:750;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.device-meta{font-size:11px;color:var(--muted);margin-top:5px;line-height:1.45}.device-buttons{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}.state-dot{width:8px;height:8px;border-radius:50%;background:#768198;display:inline-block;margin-right:5px}.state-dot.online{background:var(--ok)}.pair-box{text-align:center}.pair-box svg{width:min(300px,100%);height:auto;border-radius:12px;border:10px solid #fff;background:#fff;margin:14px auto 8px}.pair-code{font-size:27px;font-weight:850;letter-spacing:5px}.pair-url{font-size:11px;color:var(--muted);word-break:break-all;margin-top:7px}.pair-countdown{display:inline-block;margin-top:6px;padding:5px 9px;border-radius:999px;background:var(--panel3);border:1px solid var(--line);font-size:11px;color:var(--muted)}.version-badge{font-size:10px;color:var(--muted);border:1px solid var(--line);border-radius:999px;padding:3px 7px;margin-left:6px}
@media(max-width:900px){.wrap.app-wrap{padding:0}.card{width:100%;height:100vh;height:100dvh;max-height:none;border-radius:0;border:0}.top{min-height:60px;padding-left:max(10px,env(safe-area-inset-left));padding-right:max(10px,env(safe-area-inset-right))}.top .subtitle{display:none}.messages{padding:13px}.bubble{max-width:94%}.composer{padding-left:max(10px,env(safe-area-inset-left));padding-right:max(10px,env(safe-area-inset-right))}.options{grid-template-columns:repeat(2,minmax(0,1fr))}.send{min-width:72px}.brand{gap:8px}.mark{width:36px;height:36px}.mark svg{width:34px;height:34px}.roombar{padding-left:max(10px,env(safe-area-inset-left));padding-right:max(10px,env(safe-area-inset-right))}.room-note{display:none}.target-select{max-width:190px}.top-actions .ghost{padding:7px 8px;font-size:12px}}
@media(max-width:560px){.login{padding:23px 20px}.top-actions{gap:4px}.top-actions .themeBtn{display:none}.top-actions .ghost{font-size:0;padding:7px 9px}.top-actions .ghost:after{font-size:16px}.top-actions #devicesBtn:after{content:"⌘"}.top-actions #clearLocalBtn:after{content:"⌫"}.top-actions #logoutBtn:after{content:"↪"}.compose-row{grid-template-columns:42px minmax(0,1fr) 68px}.attach{width:42px}.options{grid-template-columns:1fr 1fr}.hint{display:block}.hint span{display:block;margin-top:3px}.room-btn{padding:7px 9px;font-size:12px}.bubble{max-width:97%}.roombar{display:grid;grid-template-columns:auto minmax(0,1fr)}.room-right{justify-content:flex-end}.target-select{max-width:100%;width:100%}.pair-row{grid-template-columns:1fr}.devices-actions .ghost,.devices-actions .primary{flex:1}.modal{padding:16px}.device-line{align-items:flex-start}.device-buttons .mini{flex:1}}
</style>
</head>
<body>
<div class="wrap" id="loginView">
  <section class="login">
    <div class="brandline">
      <div class="brand"><div class="mark"><svg viewBox="0 0 44 44" aria-hidden="true"><rect class="m-bg" x="3" y="3" width="38" height="38" rx="12"/><path class="m-line" d="M13 15.5h18v11H20l-5.8 4.7 1.5-4.7H13z"/><path class="m-line" d="M17 20.7h10M17 24h6"/></svg></div><div class="brandtext"><h1>BASKA SEND</h1><div class="sub">Pesan, file, dan ruang obrolan langsung ke Windows.</div></div></div>
      <button class="iconbtn themeBtn" title="Ganti tema">☀</button>
    </div>
    <div class="pair-note hidden" id="pairNotice">Tautan pairing terdeteksi. Beri nama perangkat lalu hubungkan tanpa PIN utama.</div>
    <label class="fieldlabel">Nama perangkat</label><input class="field" id="deviceName" maxlength="40" placeholder="Contoh: HP Baska / Laptop Kantor">
    <div id="pinArea"><label class="fieldlabel">PIN</label><input class="field" id="pin" type="password" inputmode="numeric" maxlength="12" placeholder="PIN utama / PIN perangkat (bukan kode pairing)"></div>
    <button class="primary wide" id="loginBtn">Masuk</button><div class="error" id="loginError"></div>
    <div class="divider" id="pairDivider">atau pairing manual</div>
    <div class="pair-row" id="pairManual"><input class="field" id="pairCode" inputmode="numeric" maxlength="6" placeholder="Kode pairing 6 digit"><button class="ghost" id="pairCodeBtn">Hubungkan</button></div>
  </section>
</div>

<div class="wrap app-wrap hidden" id="appView">
  <section class="card" id="card">
    <div class="drop-overlay" id="dropOverlay">Lepas file untuk dilampirkan</div>
    <header class="top">
      <div class="brand"><div class="mark"><svg viewBox="0 0 44 44" aria-hidden="true"><rect class="m-bg" x="3" y="3" width="38" height="38" rx="12"/><path class="m-line" d="M13 15.5h18v11H20l-5.8 4.7 1.5-4.7H13z"/><path class="m-line" d="M17 20.7h10M17 24h6"/></svg></div><div class="brandtext"><div class="title">BASKA SEND <span class="version-badge" id="versionBadge"></span></div><div class="status subtitle"><i class="dot"></i><span id="pcInfo">Terhubung</span></div></div></div>
      <div class="top-actions"><button class="iconbtn themeBtn" title="Ganti tema">☀</button><button class="ghost" id="devicesBtn">Perangkat</button><button class="ghost" id="clearLocalBtn">Bersihkan</button><button class="ghost" id="logoutBtn">Keluar</button></div>
    </header>
    <div class="roombar">
      <div class="room-tabs"><button class="room-btn active" data-room="private">Private</button><button class="room-btn" data-room="public">Ruang Umum</button></div>
      <div class="room-right"><div class="room-note" id="roomNote"></div><select class="target-select" id="targetPeer" title="Tujuan private"><option value="__pc__">BASKA SEND (PC)</option></select></div>
    </div>
    <main class="messages" id="messages"><div class="empty" id="empty"><div><strong>Siap mengirim</strong>Pesan dapat diterima Windows tanpa browser terbuka di PC.</div></div></main>
    <footer class="composer" id="composer">
      <div class="reply-chip" id="replyChip"><div class="chip-main"><b id="replyTitle">Balas pesan</b><span id="replyText"></span></div><button class="x" id="cancelReply">×</button></div>
      <div class="file-chip" id="fileChip"><div class="chip-main"><b>File terlampir</b><span id="fileName"></span></div><button class="x" id="removeFile">×</button></div>
      <div class="compose-row"><button class="attach" id="attachBtn" title="Pilih file">＋</button><textarea class="field textarea" id="text" rows="1" maxlength="10000" placeholder="Tulis pesan... (bisa paste gambar)"></textarea><button class="primary send" id="sendBtn">Kirim</button></div>
      <input id="file" type="file" hidden accept=".pdf,.docx,.xlsx,.pptx,.txt,.csv,.jpg,.jpeg,.png,.gif,.webp,.bmp">
      <details class="message-settings" open>
        <summary class="settings-summary">Pengaturan pesan</summary>
        <div class="options">
          <div class="opt"><span>Ruang</span><select id="scope"><option value="private" selected>Private</option><option value="public">Publik / Ruang Umum</option></select></div>
          <div class="opt notify-opt"><span>Mode popup PC</span><select id="notifyMode"><option value="popup">Popup modern</option><option value="windows">Dialog Windows</option><option value="toast">Notifikasi Windows</option><option value="both">Modern + notifikasi</option><option value="windows_toast">Dialog + notifikasi</option><option value="silent">Tanpa popup</option></select></div>
          <div class="opt notify-opt"><span>Durasi</span><select id="duration"><option value="5">5 detik</option><option value="10">10 detik</option><option value="15" selected>15 detik</option><option value="30">30 detik</option><option value="60">60 detik</option><option value="0">Sampai ditutup</option></select></div>
          <div class="opt notify-opt"><span>Suara</span><select id="sound"><option value="default">Default</option><option value="chime">Tring</option><option value="double">Tit-tit</option><option value="soft">Lembut</option><option value="alert">Alert</option><option value="asterisk">Asterisk</option><option value="exclamation">Peringatan</option><option value="beep">Beep</option><option value="none">Tanpa suara</option></select></div>
          <div class="opt notify-opt"><label class="tog"><input id="allowClose" type="checkbox" checked> Tombol tutup di PC</label></div>
          <div class="opt notify-opt"><label class="tog"><input id="allowReply" type="checkbox" checked> Izinkan balas</label></div>
          <div class="opt notify-opt"><label class="tog"><input id="allowCopy" type="checkbox" checked> Izinkan copy</label></div>
        </div>
      </details>
      <div class="hint"><span id="hint">File aman saja • Maksimum 50 MB</span><span id="sendStatus"></span></div><div class="progress"><i id="progress"></i></div>
    </footer>
  </section>
</div>

<div class="modal-backdrop hidden" id="modalBackdrop"><div class="modal"><h3 id="modalTitle">Konfirmasi</h3><p id="modalText"></p><div class="modal-input hidden" id="modalInputWrap"><input class="field" id="modalInput"></div><div class="modal-actions"><button class="ghost" id="modalCancel">Batal</button><button class="primary" id="modalOk">Lanjutkan</button></div></div></div>

<div class="modal-backdrop hidden" id="devicesBackdrop"><div class="modal wide-modal"><div class="devices-head"><div><h3>Perangkat</h3><p>Perangkat yang pernah terhubung ke BASKA SEND.</p></div><button class="iconbtn" id="closeDevices">×</button></div><div class="devices-actions"><button class="primary" id="pairNewBtn">Pair perangkat baru</button><button class="ghost" id="setDevicePinBtn">Atur PIN perangkat ini</button><button class="ghost hidden" id="setMainPinBtn">Ubah PIN utama</button><button class="ghost" id="refreshDevicesBtn">Muat ulang</button></div><div class="device-list" id="deviceList" style="margin-top:14px"></div></div></div>

<div class="modal-backdrop hidden" id="pairingBackdrop"><div class="modal pair-box"><h3>Pair perangkat baru</h3><p>Scan QR atau masukkan kode 6 digit pada perangkat baru. Kode hanya sekali pakai dan tersimpan aman di server sampai masa berlakunya habis.</p><div id="pairQr"></div><div class="pair-code" id="pairCodeOut"></div><div class="pair-countdown" id="pairCountdown">Menyiapkan pairing...</div><div class="pair-url" id="pairUrl"></div><div class="modal-actions" style="flex-wrap:wrap"><button class="ghost" id="copyPairBtn">Salin tautan</button><button class="ghost" id="regenPairBtn">Buat kode baru</button><button class="ghost" id="cancelPairBtn">Batalkan pairing</button><button class="primary" id="closePairBtn">Selesai</button></div></div></div>

<script>
const $=s=>document.querySelector(s), $$=s=>Array.from(document.querySelectorAll(s));
let csrf='',pollTimer=null,deviceTimer=null,busy=false,currentRoom='private',currentPartner='__pc__',lastIds={private:0,public:0},pendingFile=null,replyTarget=null,me=null,devices=[],unread={};
let pairToken=new URLSearchParams(location.search).get('pair')||'';let pairTimer=null;let activePairing=null;
const savedTheme=localStorage.getItem('pcmh_theme')||((window.matchMedia&&window.matchMedia('(prefers-color-scheme: light)').matches)?'light':'dark');
function applyTheme(theme){document.documentElement.dataset.theme=theme;localStorage.setItem('pcmh_theme',theme);const light=theme==='light';$$('.themeBtn').forEach(b=>{b.textContent=light?'☾':'☀';b.title=light?'Gunakan Dark Mode':'Gunakan Light Mode'});$('#themeMeta').setAttribute('content',light?'#f3f6fb':'#090d14')}
applyTheme(savedTheme);$$('.themeBtn').forEach(b=>b.onclick=()=>applyTheme(document.documentElement.dataset.theme==='light'?'dark':'light'));
function makePeerId(){try{if(window.crypto&&typeof window.crypto.randomUUID==='function')return 'dev_'+window.crypto.randomUUID().replace(/-/g,'')}catch(e){}try{if(window.crypto&&typeof window.crypto.getRandomValues==='function'){const b=new Uint8Array(16);window.crypto.getRandomValues(b);return 'dev_'+Array.from(b,x=>x.toString(16).padStart(2,'0')).join('')}}catch(e){}return 'dev_'+Date.now().toString(36)+Math.random().toString(36).slice(2,14)}
let peerId=localStorage.getItem('pcmh_peer_id')||makePeerId();localStorage.setItem('pcmh_peer_id',peerId);$('#deviceName').value=localStorage.getItem('pcmh_device_name')||((navigator.platform||'Perangkat').slice(0,40));
if(pairToken){$('#pairNotice').classList.remove('hidden');$('#pairNotice').textContent='Memeriksa tautan pairing...';$('#pinArea').classList.add('hidden');$('#pairDivider').classList.add('hidden');$('#pairManual').classList.add('hidden');$('#loginBtn').textContent='Hubungkan perangkat'}
function esc(s){return String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]))}
function humanBytes(n){if(!n)return'';const u=['B','KB','MB','GB'];let i=0,x=Number(n);while(x>=1024&&i<u.length-1){x/=1024;i++}return `${x.toFixed(i?1:0)} ${u[i]}`}
function fileUrl(id,preview=false){return `/api/file/${id}${preview?'?preview=1':''}`}
function formatWaktuID(v){try{const d=new Date(v),h=['Minggu','Senin','Selasa','Rabu','Kamis','Jumat','Sabtu'],b=['Januari','Februari','Maret','April','Mei','Juni','Juli','Agustus','September','Oktober','November','Desember'],p=n=>String(n).padStart(2,'0');return `${h[d.getDay()]}, ${p(d.getDate())} ${b[d.getMonth()]} ${d.getFullYear()} • ${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`}catch(e){return String(v||'')}}
function statusID(s){return ({sent:'Terkirim',delivered:'Diterima',opened:'Dibuka',replied:'Dibalas'})[s]||'Terkirim'}
function roomKey(){return currentRoom==='public'?'public':`private:${currentPartner}`}
function canRemoteClose(m){return m.sender_peer_id===peerId&&m.target_peer_id==='__pc__'&&!m.allow_close&&['popup','both','windows','windows_toast'].includes(m.notify_mode)}
function copyText(v){try{if(navigator.clipboard&&window.isSecureContext){navigator.clipboard.writeText(v);return}}catch(e){}const t=document.createElement('textarea');t.value=v;t.style.position='fixed';t.style.opacity='0';document.body.appendChild(t);t.select();try{document.execCommand('copy')}catch(e){}t.remove()}
function modal(title,text,okLabel='Lanjutkan',danger=false,input=null){return new Promise(resolve=>{const back=$('#modalBackdrop'),ok=$('#modalOk'),cancel=$('#modalCancel'),wrap=$('#modalInputWrap'),inp=$('#modalInput');$('#modalTitle').textContent=title;$('#modalText').textContent=text||'';ok.textContent=okLabel;ok.className='primary'+(danger?' danger':'');wrap.classList.toggle('hidden',!input);if(input){inp.type=input.type||'text';inp.value=input.value||'';inp.placeholder=input.placeholder||'';inp.maxLength=input.maxLength||100;inp.inputMode=input.inputMode||'text'}back.classList.remove('hidden');if(input)setTimeout(()=>inp.focus(),30);let done=false;const finish=v=>{if(done)return;done=true;back.classList.add('hidden');ok.onclick=cancel.onclick=back.onclick=null;resolve(v)};ok.onclick=()=>finish(input?inp.value:true);cancel.onclick=()=>finish(false);back.onclick=e=>{if(e.target===back)finish(false)};inp.onkeydown=e=>{if(e.key==='Enter')finish(inp.value)}})}
async function api(path,opt={}){opt.credentials='same-origin';opt.headers=opt.headers||{};if(csrf&&opt.method&&opt.method!=='GET')opt.headers['X-CSRF-Token']=csrf;const r=await fetch(path,opt);let data=null;try{data=await r.json()}catch{}if(!r.ok){const e=new Error(data?.error||`HTTP ${r.status}`);e.status=r.status;e.data=data;throw e}return data}
function roomEmpty(){if(currentRoom==='public')return '<div class="empty" id="empty"><div><strong>Ruang Umum masih kosong</strong>Semua perangkat dapat membaca dan ikut mengobrol di sini.</div></div>';const name=currentPartner==='__pc__'?'BASKA SEND':(devices.find(d=>d.peer_id===currentPartner)?.device_name||'perangkat');return `<div class="empty" id="empty"><div><strong>Belum ada pesan</strong>Chat private dengan ${esc(name)}.</div></div>`}
function updateRoomUI(){$$('.room-btn').forEach(b=>b.classList.toggle('active',b.dataset.room===currentRoom));$('#scope').value=currentRoom;const pub=currentRoom==='public';$('#targetPeer').classList.toggle('hidden',pub);$('#roomNote').textContent=pub?'Semua perangkat dapat membaca.':'Percakapan private.';updateNotifyControls()}
function updateNotifyControls(){const pcTarget=currentRoom==='public'||currentPartner==='__pc__';$$('.notify-opt').forEach(el=>el.classList.toggle('disabled',!pcTarget));if(!pcTarget)$('#sendStatus').textContent='Pesan dikirim langsung ke perangkat tujuan, tanpa popup PC.'}
async function switchRoom(room,partner=null){currentRoom=room==='public'?'public':'private';if(partner)currentPartner=partner;updateRoomUI();if(currentRoom==='private')$('#targetPeer').value=currentPartner;await loadHistory()}
function setReply(m){replyTarget=m;$('#replyChip').classList.add('on');$('#replyTitle').textContent=`Balas ${m.sender_peer_id===peerId?'pesan sendiri':(m.sender||'pesan')}`;$('#replyText').textContent=(m.text||m.file_name||'Pesan').slice(0,180);$('#text').focus()}
function clearReply(){replyTarget=null;$('#replyChip').classList.remove('on');$('#replyText').textContent=''}
async function closePopup(id,btn){btn.disabled=true;btn.textContent='Menutup...';try{await api('/api/popup/close',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message_id:id})});btn.textContent='Popup ditutup'}catch(e){btn.disabled=false;btn.textContent='Tutup popup PC';$('#sendStatus').textContent=e.message}}
async function deleteMessage(m){if(m.sender_peer_id!==peerId)return;const ok=await modal('Hapus pesan?','Pesan dihapus dari riwayat chat. File yang sudah tersimpan di Windows tidak ikut dihapus.','Hapus',true);if(!ok)return;try{await api('/api/message/delete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message_id:m.id})});document.querySelector(`[data-mid="${m.id}"]`)?.remove()}catch(e){await modal('Gagal menghapus',e.message,'Tutup')}}
async function ackOpened(m){if(m.sender_peer_id===peerId)return;try{await api('/api/message/ack',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message_id:m.id,stage:'opened'})});if(unread[m.sender_peer_id]){unread[m.sender_peer_id]=Math.max(0,Number(unread[m.sender_peer_id])-1);renderDeviceTargets()}}catch(e){}}
function render(m){const key=roomKey();lastIds[key]=Math.max(lastIds[key]||0,Number(m.id)||0);const existing=document.querySelector(`[data-mid="${m.id}"]`);if(m.deleted){existing?.remove();return}if(existing)return;$('#empty')?.remove();const mine=m.sender_peer_id===peerId;const row=document.createElement('div');row.dataset.mid=m.id;row.className='row '+(mine?'mine':'');const img=(m.mime||'').startsWith('image/');let fh='';if(m.file_name){fh=img?`<a href="${fileUrl(m.id)}"><img class="preview" src="${fileUrl(m.id,true)}" alt="${esc(m.file_name)}"></a>`:`<a class="file" href="${fileUrl(m.id)}"><span class="fi">FILE</span><span><b>${esc(m.file_name)}</b><small>${humanBytes(m.file_size)}</small></span></a>`}let quote='';if(m.reply_preview){const q=m.reply_preview;quote=`<div class="quote" data-qid="${q.id}"><b>${esc(q.sender||'Pesan')}</b><span>${esc(q.text||q.file_name||'File')}</span></div>`}let acts=['<button class="mini reply-msg">Balas</button>'];if(m.text)acts.push('<button class="mini copy-msg">Copy</button>');if(canRemoteClose(m))acts.push('<button class="mini remote-close">Tutup popup PC</button>');if(mine)acts.push('<button class="mini danger-mini delete-msg">Hapus</button>');let who=mine?'Saya':(m.sender||'BASKA SEND');if(m.sender_peer_id==='__pc__')who='BASKA SEND';const stat=mine?` • <span class="delivery" data-status-id="${m.id}">${statusID(m.status)}</span>`:'';row.innerHTML=`<div class="bubble"><div class="who">${esc(who)}${m.scope==='public'?' • Ruang Umum':''}</div>${quote}${m.text?`<div class="txt">${esc(m.text)}</div>`:''}${fh}<div class="msg-actions">${acts.join('')}</div><div class="meta">${formatWaktuID(m.created_at)}${stat}</div></div>`;row.querySelector('.reply-msg')?.addEventListener('click',()=>setReply(m));row.querySelector('.copy-msg')?.addEventListener('click',()=>copyText(m.text));row.querySelector('.remote-close')?.addEventListener('click',e=>closePopup(m.id,e.currentTarget));row.querySelector('.delete-msg')?.addEventListener('click',()=>deleteMessage(m));row.querySelector('.quote')?.addEventListener('click',()=>document.querySelector(`[data-mid="${m.reply_to_id}"]`)?.scrollIntoView({behavior:'smooth',block:'center'}));$('#messages').appendChild(row);$('#messages').scrollTop=$('#messages').scrollHeight;ackOpened(m)}
function applyUpdates(updates){(updates||[]).forEach(u=>{if(u.deleted){document.querySelector(`[data-mid="${u.id}"]`)?.remove();return}const el=document.querySelector(`[data-status-id="${u.id}"]`);if(el)el.textContent=statusID(u.status)})}
async function loadHistory(){const key=roomKey();lastIds[key]=0;$('#messages').innerHTML=roomEmpty();const room=currentRoom;const partner=currentPartner;const d=await api(`/api/messages?room=${room}&partner=${encodeURIComponent(partner)}&after=0&limit=300`);if(room!==currentRoom||partner!==currentPartner)return;d.messages.forEach(render);applyUpdates(d.updates)}
function startPoll(){clearInterval(pollTimer);pollTimer=setInterval(poll,1200);poll()}
async function poll(){try{const room=currentRoom,partner=currentPartner,key=roomKey();const d=await api(`/api/messages?room=${room}&partner=${encodeURIComponent(partner)}&after=${lastIds[key]||0}&limit=200`);if(room!==currentRoom||partner!==currentPartner)return;d.messages.forEach(render);applyUpdates(d.updates)}catch(e){if(String(e.message).includes('401'))showLogin()}}
function setPendingFile(f){pendingFile=f||null;$('#fileChip').classList.toggle('on',!!pendingFile);$('#fileName').textContent=pendingFile?`${pendingFile.name||'clipboard-image'} • ${humanBytes(pendingFile.size)}`:''}
function uploadXHR(fd){return new Promise((resolve,reject)=>{const x=new XMLHttpRequest();x.open('POST','/api/send');x.setRequestHeader('X-CSRF-Token',csrf);x.upload.onprogress=e=>{if(e.lengthComputable)$('#progress').style.width=(e.loaded/e.total*100)+'%'};x.onload=()=>{let d={};try{d=JSON.parse(x.responseText)}catch{}if(x.status>=200&&x.status<300)resolve(d);else reject(new Error(d.error||`HTTP ${x.status}`))};x.onerror=()=>reject(new Error('Koneksi gagal'));x.send(fd)})}
async function send(){if(busy)return;const txt=$('#text').value.trim(),f=pendingFile;if(!txt&&!f)return;busy=true;$('#sendBtn').disabled=true;$('#sendStatus').textContent='Mengirim...';$('#progress').style.width='4%';const fd=new FormData();fd.append('text',txt);if(f)fd.append('file',f,f.name||'clipboard.png');fd.append('scope',currentRoom);fd.append('target_peer_id',currentRoom==='private'?currentPartner:'__public__');fd.append('reply_to_id',replyTarget?String(replyTarget.id):'');fd.append('notify_mode',$('#notifyMode').value);fd.append('duration',$('#duration').value);fd.append('sound',$('#sound').value);fd.append('allow_close',$('#allowClose').checked?'1':'0');fd.append('allow_reply',$('#allowReply').checked?'1':'0');fd.append('allow_copy',$('#allowCopy').checked?'1':'0');try{const d=await uploadXHR(fd);$('#text').value='';$('#file').value='';setPendingFile(null);clearReply();$('#sendStatus').textContent='Terkirim';if(d.message)render(d.message);setTimeout(()=>{if($('#sendStatus').textContent==='Terkirim')$('#sendStatus').textContent=''},1800)}catch(e){$('#sendStatus').textContent=e.message}finally{$('#progress').style.width='0';$('#sendBtn').disabled=false;busy=false}}
function showApp(){$('#loginView').classList.add('hidden');$('#appView').classList.remove('hidden')}
function showLogin(){$('#appView').classList.add('hidden');$('#loginView').classList.remove('hidden');clearInterval(pollTimer);clearInterval(deviceTimer)}
async function finishLogin(d,device){csrf=d.csrf;peerId=d.peer_id||peerId;localStorage.setItem('pcmh_peer_id',peerId);localStorage.setItem('pcmh_device_name',device);me=d;$('#pcInfo').textContent=`${d.pc_name} • ${device}`;$('#versionBadge').textContent='v'+(d.version||'');$('#hint').textContent=`File aman • maks ${d.max_upload_mb} MB • disimpan di ${d.received_files_dir}`;$('#setMainPinBtn')?.classList.toggle('hidden',!d.local_admin);$('#setDevicePinBtn')?.classList.toggle('hidden',!!d.local_admin);const paired=d.auth_mode==='pairing';if(pairToken){pairToken='';history.replaceState(null,'',location.pathname);$('#pairNotice').classList.add('hidden');$('#pinArea').classList.remove('hidden');$('#pairDivider').classList.remove('hidden');$('#pairManual').classList.remove('hidden');$('#loginBtn').textContent='Masuk'}showApp();await refreshDevices();currentRoom='private';currentPartner='__pc__';updateRoomUI();await loadHistory();startPoll();clearInterval(deviceTimer);deviceTimer=setInterval(refreshDevices,10000);if(paired){setTimeout(async()=>{const value=await modal('Buat PIN perangkat','Pairing berhasil. Buat PIN 4-12 digit untuk perangkat ini agar setelah logout Anda bisa masuk kembali tanpa PIN utama atau pairing baru. Anda juga bisa mengaturnya nanti dari menu Perangkat.','Simpan PIN',false,{type:'password',inputMode:'numeric',maxLength:12,placeholder:'4-12 digit'});if(value===false||!String(value).trim())return;try{await api('/api/device/pin',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({pin:String(value).trim()})});await modal('PIN perangkat tersimpan','PIN khusus perangkat berhasil dibuat.','Tutup');await refreshDevices()}catch(e){await modal('PIN belum tersimpan',e.message||'Gagal menyimpan PIN perangkat.','Tutup')}} ,350)}}
function useNormalLogin(message=''){pairToken='';history.replaceState(null,'',location.pathname);$('#pairNotice').classList.add('hidden');$('#pinArea').classList.remove('hidden');$('#pairDivider').classList.remove('hidden');$('#pairManual').classList.remove('hidden');$('#loginBtn').textContent='Masuk';if(message)$('#loginError').textContent=message}
async function validatePairLink(){if(!pairToken)return;try{const d=await api('/api/pairing/status?value='+encodeURIComponent(pairToken));if(d.status==='valid'){$('#pairNotice').textContent=`Tautan pairing aktif • berlaku ${formatCountdown(d.expires_in||0)}. Beri nama perangkat lalu Hubungkan.`;return}useNormalLogin(d.message||'Tautan pairing tidak dapat digunakan.')}catch(e){useNormalLogin(e.message||'Tautan pairing tidak dapat digunakan.')}}
async function login(){const device=$('#deviceName').value.trim()||'Perangkat';const pin=$('#pin').value.trim();if(!pairToken&&!pin){$('#loginError').textContent='Masukkan PIN terlebih dahulu.';$('#pin').focus();return}const btn=$('#loginBtn'),old=btn.textContent;btn.disabled=true;btn.textContent='Memeriksa...';$('#loginError').textContent='';try{const path=pairToken?'/api/pairing/accept':'/api/login';const body=pairToken?{pairing:pairToken,device_name:device,peer_id:peerId}:{pin,device_name:device,peer_id:peerId};const d=await api(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});await finishLogin(d,device)}catch(e){if(pairToken&&[404,409,410].includes(Number(e.status||0)))useNormalLogin(e.message);else $('#loginError').textContent=e.message||'Login gagal.'}finally{btn.disabled=false;btn.textContent=pairToken?'Hubungkan perangkat':'Masuk'}}
async function loginWithPairCode(){const raw=$('#pairCode').value.trim(),code=raw.replace(/\D/g,''),device=$('#deviceName').value.trim()||'Perangkat';if(!/^\d{6}$/.test(code)){$('#loginError').textContent='Kode pairing harus 6 digit dari menu Perangkat → Pair perangkat baru.';return}const btn=$('#pairCodeBtn'),old=btn.textContent;btn.disabled=true;btn.textContent='Memeriksa...';$('#loginError').textContent='';try{const d=await api('/api/pairing/accept',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({pairing:code,device_name:device,peer_id:peerId})});await finishLogin(d,device)}catch(e){$('#loginError').textContent=e.message||'Pairing gagal.'}finally{btn.disabled=false;btn.textContent=old}}
async function checkSession(){try{const d=await api('/api/me');await finishLogin(d,d.device_name);return}catch(e){}try{const device=$('#deviceName').value.trim()||'PC Lokal';const d=await api('/api/local-login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({peer_id:peerId,device_name:device})});await finishLogin(d,device)}catch(e){showLogin()}}
async function refreshDevices(){if(!csrf)return;try{const d=await api('/api/devices');devices=d.devices||[];unread=d.unread||{};if(me){me.is_admin=d.is_admin;me.local_admin=d.local_admin}renderDeviceTargets();const total=Object.values(unread).reduce((a,b)=>a+Number(b||0),0);document.title=total?`(${total}) BASKA SEND`:'BASKA SEND';if(total&&$('#sendStatus').textContent===''){$('#sendStatus').textContent=`${total} pesan private belum dibuka`};if(!$('#devicesBackdrop').classList.contains('hidden'))renderDevices()}catch(e){}}
function renderDeviceTargets(){const sel=$('#targetPeer'),keep=currentPartner,pcN=Number(unread['__pc__']||0);sel.innerHTML=`<option value="__pc__">BASKA SEND (PC)${pcN?' • '+pcN+' baru':''}</option>`;devices.filter(d=>!d.revoked&&!d.blocked&&d.peer_id!==peerId).forEach(d=>{const o=document.createElement('option'),n=Number(unread[d.peer_id]||0);o.value=d.peer_id;o.textContent=`${d.device_name}${d.online?' • online':' • offline'}${n?' • '+n+' baru':''}`;sel.appendChild(o)});if(Array.from(sel.options).some(o=>o.value===keep))sel.value=keep;else{currentPartner='__pc__';sel.value='__pc__'}}
function renderDevices(){const box=$('#deviceList');box.innerHTML='';const all=devices;if(!all.length){box.innerHTML='<div class="device-item">Belum ada perangkat.</div>';return}if(me?.is_admin&&!me?.local_admin){const info=document.createElement('div');info.className='device-item';info.innerHTML='<b>Manajemen perangkat dikunci.</b><div class="device-meta">Untuk Blokir, Buka blokir, Reset PIN, Cabut/Pulihkan akses, atau Hapus perangkat, buka WebApp dari PC server melalui <code>http://localhost:8765</code> atau <code>http://127.0.0.1:8765</code> lalu login dengan PIN utama.</div>';box.appendChild(info)}all.forEach(d=>{const el=document.createElement('div');el.className='device-item';const last=formatWaktuID(d.last_seen),state=d.blocked?' • DIBLOKIR':d.revoked?' • akses dicabut':'';el.innerHTML=`<div class="device-line"><div class="device-name"><span class="state-dot ${d.online?'online':''}"></span>${esc(d.device_name)} ${d.is_current?'(perangkat ini)':''}${state}</div><small>${d.has_pin?'PIN khusus aktif':''}</small></div><div class="device-meta">IP: ${esc(d.last_ip||'-')}<br>Terakhir aktif: ${last}${Number(unread[d.peer_id]||0)?`<br><b>${Number(unread[d.peer_id])} pesan baru</b>`:''}</div><div class="device-buttons"></div>`;const btns=el.querySelector('.device-buttons');if(!d.is_current&&!d.revoked&&!d.blocked){const chat=document.createElement('button');chat.className='mini';chat.textContent='Chat private';chat.onclick=async()=>{$('#devicesBackdrop').classList.add('hidden');currentPartner=d.peer_id;await switchRoom('private',d.peer_id)};btns.appendChild(chat)}if(me?.local_admin&&!d.is_current){const add=(label,action,danger=false)=>{const b=document.createElement('button');b.className='mini'+(danger?' danger-mini':'');b.textContent=label;b.onclick=()=>localDeviceAction(d,action,label);btns.appendChild(b)};if(d.blocked)add('Buka blokir','unblock');else add('Blokir','block',true);if(d.revoked)add('Pulihkan akses','restore');else add('Cabut akses','revoke',true);if(d.has_pin)add('Reset PIN','reset_pin',true);add('Hapus perangkat','delete',true)}box.appendChild(el)});$('#pairNewBtn').classList.toggle('hidden',!me?.local_admin)}
async function localDeviceAction(d,action,label){let detail=`${label} perangkat “${d.device_name}”?`;if(action==='delete')detail+='\n\nPendaftaran perangkat akan dihapus. Riwayat chat tidak ikut dihapus.';if(action==='block')detail+='\n\nSemua sesi perangkat akan diputus dan login dari perangkat ini ditolak sampai dibuka blokir.';if(action==='reset_pin')detail+='\n\nPIN khusus perangkat akan dihapus dan semua sesi perangkat diputus.';if(!await modal('Manajemen perangkat lokal',detail,label))return;try{await api('/api/local/device/action',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({peer_id:d.peer_id,action})});await refreshDevices();renderDevices()}catch(e){await modal('Aksi gagal',e.message,'Tutup')}}

async function openDevices(){await refreshDevices();renderDevices();$('#devicesBackdrop').classList.remove('hidden')}
async function setOwnPin(){const value=await modal('Atur PIN perangkat','PIN ini hanya berlaku untuk perangkat/browser ini. PIN utama tetap dapat digunakan oleh admin.','Simpan',false,{type:'password',inputMode:'numeric',maxLength:12,placeholder:'4-12 digit'});if(value===false)return;try{await api('/api/device/pin',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({pin:value})});await modal('PIN tersimpan','PIN khusus perangkat berhasil diaktifkan.','Tutup');refreshDevices()}catch(e){await modal('Gagal',e.message,'Tutup')}}
async function setMainPinUI(){if(!me?.local_admin){await modal('Akses ditolak','PIN utama hanya dapat diubah dari PC server.','Tutup');return}const value=await modal('Ubah PIN utama','Masukkan PIN utama baru 4-12 digit. PIN ini dipakai untuk login dari perangkat lain.','Simpan PIN',false,{type:'password',inputMode:'numeric',maxLength:12,placeholder:'4-12 digit'});if(value===false)return;try{await api('/api/local/main-pin',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({pin:String(value).trim()})});await modal('PIN utama diperbarui','PIN utama baru sudah aktif dan dapat digunakan dari perangkat lain.','Tutup')}catch(e){await modal('Gagal mengubah PIN',e.message,'Tutup')}}
async function revokeDeviceUI(d){if(!await modal('Cabut akses perangkat?',`${d.device_name} akan langsung logout dan tidak dapat memakai PIN perangkat/pairing lama. PIN utama masih bisa mendaftarkannya kembali.`,`Cabut akses`,true))return;try{await api('/api/device/revoke',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({peer_id:d.peer_id})});await refreshDevices()}catch(e){await modal('Gagal',e.message,'Tutup')}}
function formatCountdown(sec){sec=Math.max(0,Number(sec)||0);const m=Math.floor(sec/60),s=Math.floor(sec%60);return `${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`}
function stopPairTimer(){if(pairTimer){clearInterval(pairTimer);pairTimer=null}}
function startPairTimer(expiresAt){stopPairTimer();const tick=()=>{const left=Math.max(0,Math.ceil(Number(expiresAt)-Date.now()/1000));$('#pairCountdown').textContent=left?`Berlaku ${formatCountdown(left)} • sekali pakai`:'Kedaluwarsa • buat kode baru';if(!left)stopPairTimer()};tick();pairTimer=setInterval(tick,500)}
async function createPairingUI(){try{const d=await api('/api/pairing/create',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ttl:600})});activePairing=d;$('#pairQr').innerHTML=d.qr_svg;$('#pairCodeOut').textContent=d.code;$('#pairUrl').textContent=d.url;$('#copyPairBtn').onclick=()=>{copyText(d.url);$('#copyPairBtn').textContent='Tersalin';setTimeout(()=>$('#copyPairBtn').textContent='Salin tautan',1200)};startPairTimer(d.expires_at);$('#pairingBackdrop').classList.remove('hidden')}catch(e){await modal('Pairing gagal',e.message,'Tutup')}}
async function cancelPairingUI(closeAfter=false){try{await api('/api/pairing/cancel',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});stopPairTimer();activePairing=null;$('#pairCountdown').textContent='Pairing dibatalkan';if(closeAfter)$('#pairingBackdrop').classList.add('hidden')}catch(e){await modal('Gagal membatalkan pairing',e.message,'Tutup')}}
$('#loginBtn').onclick=login;$('#pin').addEventListener('keydown',e=>{if(e.key==='Enter')login()});$('#pairCodeBtn').onclick=loginWithPairCode;$('#pairCode').addEventListener('keydown',e=>{if(e.key==='Enter')loginWithPairCode()});$('#sendBtn').onclick=send;$('#text').addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send()}});$('#text').addEventListener('paste',e=>{const fs=Array.from(e.clipboardData?.files||[]);if(fs.length)setPendingFile(fs[0])});$('#attachBtn').onclick=()=>$('#file').click();$('#file').onchange=()=>setPendingFile($('#file').files[0]||null);$('#removeFile').onclick=()=>{$('#file').value='';setPendingFile(null)};$('#cancelReply').onclick=clearReply;
$$('.room-btn').forEach(b=>b.onclick=()=>switchRoom(b.dataset.room));$('#scope').onchange=()=>switchRoom($('#scope').value);$('#targetPeer').onchange=async()=>{currentPartner=$('#targetPeer').value;await switchRoom('private',currentPartner)};
$('#devicesBtn').onclick=openDevices;$('#closeDevices').onclick=()=>$('#devicesBackdrop').classList.add('hidden');$('#devicesBackdrop').onclick=e=>{if(e.target===$('#devicesBackdrop'))$('#devicesBackdrop').classList.add('hidden')};$('#refreshDevicesBtn').onclick=refreshDevices;$('#setDevicePinBtn').onclick=setOwnPin;$('#setMainPinBtn').onclick=setMainPinUI;$('#pairNewBtn').onclick=createPairingUI;$('#regenPairBtn').onclick=createPairingUI;$('#cancelPairBtn').onclick=()=>cancelPairingUI(false);$('#closePairBtn').onclick=()=>{$('#pairingBackdrop').classList.add('hidden');stopPairTimer()};$('#pairingBackdrop').onclick=e=>{if(e.target===$('#pairingBackdrop')){$('#pairingBackdrop').classList.add('hidden');stopPairTimer()}};
$('#logoutBtn').onclick=async()=>{if(!await modal('Keluar dari BASKA SEND?','Sesi pada perangkat ini akan diakhiri.','Keluar'))return;try{await api('/api/logout',{method:'POST'})}catch{}csrf='';showLogin()};
$('#clearLocalBtn').onclick=async()=>{const publicMsg=me?.local_admin?'Semua pesan Ruang Umum akan dihapus dari server.':'Di Ruang Umum, hanya pesan publik yang Anda kirim yang akan dihapus; pesan pengguna lain tetap ada.';const detail=currentRoom==='private'?'Seluruh riwayat percakapan private yang sedang dibuka akan dihapus dari server. File yang sudah diterima di Windows tidak ikut dihapus.':publicMsg+'\n\nFile yang sudah diterima di Windows tidak ikut dihapus.';if(!await modal('Bersihkan pesan?',detail,'Hapus pesan'))return;try{const d=await api('/api/messages/clear',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({room:currentRoom,partner:currentPartner})});lastIds[currentRoom]=0;$('#messages').innerHTML=roomEmpty();await loadHistory();await modal('Pesan dibersihkan',`${d.count||0} pesan dihapus dari server.`,`OK`)}catch(e){await modal('Gagal membersihkan pesan',e.message,'Tutup')}};
['notifyMode','duration','sound','allowClose','allowReply','allowCopy'].forEach(id=>{const el=$('#'+id),key='pcmh_'+id;const v=localStorage.getItem(key);if(v!==null){if(el.type==='checkbox')el.checked=v==='1';else el.value=v}el.addEventListener('change',()=>localStorage.setItem(key,el.type==='checkbox'?(el.checked?'1':'0'):el.value))});
let dragDepth=0;const card=$('#card');['dragenter','dragover'].forEach(ev=>card.addEventListener(ev,e=>{e.preventDefault();dragDepth++;card.classList.add('dragging')}));card.addEventListener('dragleave',e=>{e.preventDefault();dragDepth=Math.max(0,dragDepth-1);if(!dragDepth)card.classList.remove('dragging')});card.addEventListener('drop',e=>{e.preventDefault();dragDepth=0;card.classList.remove('dragging');const f=e.dataTransfer?.files?.[0];if(f)setPendingFile(f)});
if(pairToken){showLogin();validatePairLink()}else{checkSession()}
</script>
</body>
</html>'''



class AppState:
    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg
        self.sessions = SessionStore(int(cfg.get("session_hours", SESSION_HOURS)))
        self.login_guard = LoginGuard()
        self.popup_queue: queue.Queue[int] = queue.Queue()
        self.control_queue: queue.Queue[Tuple[str, int]] = queue.Queue()
        self.shutdown_event = threading.Event()
        self.httpd: Optional[ThreadingHTTPServer] = None
        self.notifications_paused = False

    def create_reply(self, peer_id: str, text: str, file_path: Optional[str], scope: str = "private", reply_to_id: Optional[int] = None) -> int:
        stored_path = name = mime = None
        size = 0
        if file_path:
            stored_path, name, size, mime = save_local_reply_file(self.cfg, file_path)
        if not text.strip() and not stored_path:
            raise ValueError("Balasan kosong.")
        target = "__public__" if scope == "public" else str(peer_id)
        mid = insert_message(
            peer_id=str(peer_id),
            direction="to_device",
            sender=str(self.cfg.get("device_name", "BASKA SEND")),
            text=text.strip(),
            file_path=stored_path,
            file_name=name,
            mime=mime,
            file_size=size,
            notify_mode="silent",
            duration=0,
            desktop_delivered=1,
            scope=scope,
            sender_peer_id="__pc__",
            target_peer_id=target,
            reply_to_id=reply_to_id,
            delivered_at=None if scope == "private" else now_iso(),
        )
        return mid


class Handler(BaseHTTPRequestHandler):
    server_version = "SendToCom/2.2.4"
    app_state: AppState = None  # type: ignore

    def log_message(self, fmt: str, *args) -> None:
        log(f"HTTP {self.client_address[0]} - {fmt % args}")

    def _source_allowed(self) -> bool:
        if not self.app_state.cfg.get("lan_only", True):
            return True
        return is_private_source(self.client_address[0])

    def _security_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data: blob:; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'",
        )
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")

    def _json(self, code: int, obj: Dict[str, Any], extra_headers: Optional[Dict[str, str]] = None) -> None:
        raw = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self._security_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        if extra_headers:
            for k, v in extra_headers.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(raw)

    def _html(self, code: int, html: str) -> None:
        raw = html.encode("utf-8")
        self.send_response(code)
        self._security_headers()
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _binary(self, code: int, data: bytes, content_type: str, cache: str = "public, max-age=86400") -> None:
        self.send_response(code)
        self._security_headers()
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", cache)
        self.end_headers()
        self.wfile.write(data)

    def _read_body(self, max_bytes: Optional[int] = None) -> bytes:
        n = int(self.headers.get("Content-Length", "0") or 0)
        if n < 0:
            raise ValueError("Content-Length tidak valid")
        if max_bytes is not None and n > max_bytes:
            raise OverflowError("Payload terlalu besar")
        return self.rfile.read(n)

    def _json_body(self, max_bytes: int = 256 * 1024) -> Dict[str, Any]:
        raw = self._read_body(max_bytes)
        return json.loads(raw.decode("utf-8") or "{}")

    def _session(self) -> Optional[Session]:
        raw = self.headers.get("Cookie", "")
        c = SimpleCookie()
        try:
            c.load(raw)
        except Exception:
            return None
        morsel = c.get(SESSION_COOKIE)
        return self.app_state.sessions.get(morsel.value if morsel else "")

    def _require_auth(self, csrf: bool = False) -> Optional[Session]:
        s = self._session()
        if not s:
            self._json(401, {"error": "Sesi tidak valid. Silakan login lagi."})
            return None
        row = get_device(s.peer_id)
        if row is not None:
            keys = set(row.keys())
            local_admin = bool(s.is_admin and is_local_machine_source(self.client_address[0]))
            if bool(row["revoked"]) and not local_admin:
                self.app_state.sessions.delete_peer(s.peer_id)
                self._json(401, {"error": "Akses perangkat ini telah dicabut."})
                return None
            if "blocked" in keys and bool(row["blocked"]) and not local_admin:
                self.app_state.sessions.delete_peer(s.peer_id)
                self._json(403, {"error": "Perangkat ini diblokir oleh PC utama."})
                return None
        touch_device(s.peer_id, s.device_name, self.client_address[0])
        if csrf:
            supplied = self.headers.get("X-CSRF-Token", "")
            if not supplied or not hmac.compare_digest(s.csrf, supplied):
                self._json(403, {"error": "CSRF token tidak valid."})
                return None
        return s

    def _parse_multipart(self, body: bytes) -> Tuple[Dict[str, str], Optional[Tuple[str, bytes, str]]]:
        ctype = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in ctype:
            raise ValueError("Content-Type harus multipart/form-data")
        pseudo = (f"Content-Type: {ctype}\r\nMIME-Version: 1.0\r\n\r\n").encode("utf-8") + body
        msg = BytesParser(policy=email_default_policy).parsebytes(pseudo)
        if not msg.is_multipart():
            raise ValueError("Multipart tidak valid")
        fields: Dict[str, str] = {}
        file_info = None
        for part in msg.iter_parts():
            name = part.get_param("name", header="content-disposition")
            if not name:
                continue
            filename = part.get_filename()
            payload = part.get_payload(decode=True) or b""
            if filename is not None and name == "file":
                file_info = (filename, payload, part.get_content_type())
            else:
                charset = part.get_content_charset() or "utf-8"
                fields[name] = payload.decode(charset, errors="replace")
        return fields, file_info

    def _cookie(self, s: Session) -> str:
        max_age = int(self.app_state.cfg.get("session_hours", 24)) * 3600
        return f"{SESSION_COOKIE}={s.token}; Path=/; HttpOnly; SameSite=Strict; Max-Age={max_age}"

    def _session_payload(self, s: Session) -> Dict[str, Any]:
        return {
            "ok": True,
            "csrf": s.csrf,
            "peer_id": s.peer_id,
            "device_name": s.device_name,
            "pc_name": str(self.app_state.cfg.get("device_name", APP_TITLE)),
            "max_upload_mb": int(self.app_state.cfg.get("max_upload_mb", 50)),
            "allowed_extensions": self.app_state.cfg.get("allowed_extensions", []),
            "received_files_dir": str(received_files_dir(self.app_state.cfg)),
            "is_admin": bool(s.is_admin),
            "local_admin": bool(s.is_admin and is_local_machine_source(self.client_address[0])),
            "auth_mode": s.auth_mode,
            "version": VERSION,
        }

    def do_GET(self) -> None:
        if not self._source_allowed():
            self._json(403, {"error": "Akses hanya diizinkan dari jaringan lokal."})
            return
        path = urllib.parse.urlsplit(self.path)
        if path.path == "/":
            self._html(200, WEB_APP)
            return
        if path.path == "/favicon.ico":
            self._binary(200, FAVICON_ICO, "image/x-icon")
            return
        if path.path == "/favicon.png":
            self._binary(200, FAVICON_PNG, "image/png")
            return
        if path.path == "/manifest.webmanifest":
            manifest = json.dumps({
                "name": APP_TITLE,
                "short_name": "BASKA SEND",
                "start_url": "/",
                "display": "standalone",
                "background_color": "#090d14",
                "theme_color": "#4c7dff",
                "icons": [{"src": "/favicon.png", "sizes": "64x64", "type": "image/png"}],
            }, ensure_ascii=False).encode("utf-8")
            self._binary(200, manifest, "application/manifest+json; charset=utf-8", "no-cache")
            return
        if path.path == "/api/pairing/status":
            qs = urllib.parse.parse_qs(path.query)
            value = qs.get("value", [""])[0]
            state = inspect_pairing(value)
            state["message"] = "Pairing aktif." if state.get("ok") else pairing_status_message(str(state.get("status")))
            self._json(200, state)
            return
        if path.path == "/api/health":
            self._json(200, {"ok": True, "version": VERSION})
            return
        if path.path == "/api/me":
            s = self._require_auth(False)
            if not s:
                return
            self._json(200, self._session_payload(s))
            return
        if path.path == "/api/devices":
            s = self._require_auth(False)
            if not s:
                return
            local_admin = bool(s.is_admin and is_local_machine_source(self.client_address[0]))
            self._json(200, {"devices": list_devices(s.peer_id, include_revoked=local_admin), "is_admin": bool(s.is_admin), "local_admin": local_admin, "unread": unread_counts(s.peer_id)})
            return
        if path.path == "/api/messages":
            s = self._require_auth(False)
            if not s:
                return
            qs = urllib.parse.parse_qs(path.query)
            try:
                after = int(qs.get("after", ["0"])[0])
                limit = int(qs.get("limit", ["200"])[0])
            except Exception:
                after, limit = 0, 200
            room = "public" if qs.get("room", ["private"])[0] == "public" else "private"
            partner = qs.get("partner", ["__pc__"])[0] if room == "private" else None
            messages = get_messages(s.peer_id, room, after, limit, partner)
            changed = False
            for m in messages:
                if m.get("sender_peer_id") != s.peer_id and (room == "public" or m.get("target_peer_id") == s.peer_id):
                    if not m.get("delivered_at"):
                        acknowledge_message(s.peer_id, int(m["id"]), "delivered")
                        changed = True
            if changed:
                messages = get_messages(s.peer_id, room, after, limit, partner)
            updates = get_message_updates(s.peer_id, room, 300, partner).get("updates", [])
            self._json(200, {"messages": messages, "updates": updates, "room": room, "partner": partner})
            return
        if path.path.startswith("/api/file/"):
            s = self._require_auth(False)
            if not s:
                return
            try:
                mid = int(path.path.rsplit("/", 1)[1])
            except Exception:
                self._json(400, {"error": "ID file tidak valid"})
                return
            row = get_message(mid)
            if not row or bool(row["deleted"]) or not row["file_path"]:
                self._json(404, {"error": "File tidak ditemukan"})
                return
            if row["scope"] != "public" and s.peer_id not in {row["sender_peer_id"], row["target_peer_id"]}:
                self._json(403, {"error": "File bukan milik percakapan perangkat ini"})
                return
            p = Path(row["file_path"])
            if not p.exists() or not is_served_file(self.app_state.cfg, p):
                self._json(404, {"error": "File tidak tersedia"})
                return
            preview = urllib.parse.parse_qs(path.query).get("preview", ["0"])[0] == "1"
            ext = Path(row["file_name"] or "").suffix.lower()
            if preview and ext not in PREVIEWABLE_EXTENSIONS:
                self._json(403, {"error": "Preview tidak tersedia untuk tipe file ini"})
                return
            data = p.read_bytes()
            self.send_response(200)
            self._security_headers()
            self.send_header("Content-Type", row["mime"] or "application/octet-stream")
            disposition = "inline" if preview else "attachment"
            qname = urllib.parse.quote(row["file_name"] or "file")
            self.send_header("Content-Disposition", f"{disposition}; filename*=UTF-8''{qname}")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        self._json(404, {"error": "Not found"})

    def do_POST(self) -> None:
        if not self._source_allowed():
            self._json(403, {"error": "Akses hanya diizinkan dari jaringan lokal."})
            return
        path = urllib.parse.urlsplit(self.path).path

        if path == "/api/local-login":
            if not is_local_machine_source(self.client_address[0]):
                self._json(403, {"error": "Login otomatis hanya tersedia dari PC yang menjalankan BASKA SEND."})
                return
            try:
                data = self._json_body()
            except Exception:
                data = {}
            peer_id = str(data.get("peer_id", ""))[:64]
            if not re.fullmatch(r"[A-Za-z0-9_-]{8,64}", peer_id):
                peer_id = "local_" + uuid.uuid4().hex
            device = re.sub(r"[^\w .()\-]", "", str(data.get("device_name", "PC Lokal")), flags=re.UNICODE).strip()[:40] or "PC Lokal"
            existing_device = get_device(peer_id)
            if existing_device is not None:
                keys = set(existing_device.keys())
                if "blocked" in keys and bool(existing_device["blocked"]):
                    unblock_device(peer_id)
                if bool(existing_device["revoked"]):
                    restore_device(peer_id)
            upsert_device(peer_id, device, self.client_address[0], allow_unrevoke=True)
            s = self.app_state.sessions.create(peer_id, device, is_admin=True, auth_mode="local_auto")
            self.app_state.login_guard.success(self.client_address[0])
            self._json(200, self._session_payload(s), {"Set-Cookie": self._cookie(s)})
            return

        if path == "/api/local/main-pin":
            s = self._require_auth(True)
            if not s:
                return
            if not (s.is_admin and is_local_machine_source(self.client_address[0])):
                self._json(403, {"error": "PIN utama hanya dapat diubah dari PC server."})
                return
            try:
                data = self._json_body()
                new_pin = str(data.get("pin", "")).strip()
                set_pin(new_pin)
                self.app_state.cfg = load_config()
            except ValueError as e:
                self._json(400, {"error": str(e)})
                return
            except Exception as e:
                self._json(500, {"error": f"Gagal mengubah PIN utama: {e}"})
                return
            self._json(200, {"ok": True})
            return

        if path == "/api/login":
            wait = self.app_state.login_guard.is_locked(self.client_address[0])
            if wait:
                self._json(429, {"error": f"Terlalu banyak percobaan gagal. Coba lagi sekitar {wait} detik."})
                return
            try:
                data = self._json_body()
            except Exception:
                self._json(400, {"error": "Payload login tidak valid."})
                return
            pin = str(data.get("pin", ""))
            peer_id = str(data.get("peer_id", ""))[:64]
            if not re.fullmatch(r"[A-Za-z0-9_-]{8,64}", peer_id):
                peer_id = "dev_" + uuid.uuid4().hex
            device = re.sub(r"[^\w .()\-]", "", str(data.get("device_name", "Perangkat")), flags=re.UNICODE).strip()[:40] or "Perangkat"
            existing_device = get_device(peer_id)
            if existing_device is not None and "blocked" in set(existing_device.keys()) and bool(existing_device["blocked"]) and not is_loopback_source(self.client_address[0]):
                self.app_state.login_guard.failed(self.client_address[0])
                self._json(403, {"error": "Perangkat ini diblokir oleh PC utama."})
                return
            global_ok = verify_main_pin_with_legacy_recovery(self.app_state.cfg, pin)
            if global_ok and is_loopback_source(self.client_address[0]) and existing_device is not None and "blocked" in set(existing_device.keys()) and bool(existing_device["blocked"]):
                unblock_device(peer_id)
            device_ok = False if global_ok else verify_device_pin(peer_id, pin)
            if not global_ok and not device_ok:
                self.app_state.login_guard.failed(self.client_address[0])
                if existing_device is not None:
                    keys = set(existing_device.keys())
                    if bool(existing_device["revoked"]):
                        message = "Akses perangkat ini telah dicabut. Gunakan PIN utama untuk mendaftarkan kembali, atau pulihkan akses dari localhost PC."
                    elif bool(existing_device["pin_hash_b64"]):
                        message = "PIN tidak cocok. Gunakan PIN utama atau PIN khusus perangkat ini."
                    else:
                        message = "PIN tidak cocok. Perangkat ini belum memiliki PIN khusus; gunakan PIN utama atau lakukan pairing baru."
                else:
                    message = "PIN tidak cocok. Gunakan PIN utama yang aktif. Dari PC server, buka BASKA SEND tanpa PIN lalu pilih Perangkat → Ubah PIN utama jika perlu."
                self._json(401, {"error": message})
                return
            self.app_state.login_guard.success(self.client_address[0])
            upsert_device(peer_id, device, self.client_address[0], allow_unrevoke=bool(global_ok))
            s = self.app_state.sessions.create(peer_id, device, is_admin=bool(global_ok), auth_mode="main_pin" if global_ok else "device_pin")
            try:
                FIRST_PIN_PATH.unlink(missing_ok=True)
            except Exception:
                pass
            self._json(200, self._session_payload(s), {"Set-Cookie": self._cookie(s)})
            return

        if path == "/api/pairing/accept":
            wait = self.app_state.login_guard.is_locked(self.client_address[0])
            if wait:
                self._json(429, {"error": f"Terlalu banyak percobaan gagal. Coba lagi sekitar {wait} detik."})
                return
            try:
                data = self._json_body()
                pairing = str(data.get("pairing", "")).strip()
                peer_id = str(data.get("peer_id", ""))[:64]
                if not re.fullmatch(r"[A-Za-z0-9_-]{8,64}", peer_id):
                    peer_id = "dev_" + uuid.uuid4().hex
                device = re.sub(r"[^\w .()\-]", "", str(data.get("device_name", "Perangkat")), flags=re.UNICODE).strip()[:40] or "Perangkat"
            except Exception:
                self._json(400, {"error": "Data pairing tidak valid."})
                return
            existing_device = get_device(peer_id)
            if existing_device is not None and "blocked" in set(existing_device.keys()) and bool(existing_device["blocked"]):
                self._json(403, {"error": "Perangkat ini masih diblokir. Buka blokir dari localhost PC terlebih dahulu."})
                return
            pair_result = consume_pairing(pairing, peer_id)
            if not pair_result.get("ok"):
                pstatus = str(pair_result.get("status", "invalid"))
                if pstatus == "invalid":
                    self.app_state.login_guard.failed(self.client_address[0])
                http_code = 404 if pstatus == "invalid" else 409 if pstatus in {"used", "canceled"} else 410
                self._json(http_code, {"error": pairing_status_message(pstatus), "pairing_status": pstatus})
                return
            self.app_state.login_guard.success(self.client_address[0])
            upsert_device(peer_id, device, self.client_address[0], allow_unrevoke=True)
            s = self.app_state.sessions.create(peer_id, device, is_admin=False, auth_mode="pairing")
            self._json(200, self._session_payload(s), {"Set-Cookie": self._cookie(s)})
            return

        if path == "/api/logout":
            s = self._require_auth(True)
            if not s:
                return
            raw = self.headers.get("Cookie", "")
            c = SimpleCookie()
            try:
                c.load(raw)
                tok = c.get(SESSION_COOKIE)
                if tok:
                    self.app_state.sessions.delete(tok.value)
            except Exception:
                pass
            self._json(200, {"ok": True}, {"Set-Cookie": f"{SESSION_COOKIE}=; Path=/; Max-Age=0; HttpOnly; SameSite=Strict"})
            return

        if path == "/api/device/pin":
            s = self._require_auth(True)
            if not s:
                return
            try:
                data = self._json_body()
                set_device_pin(s.peer_id, str(data.get("pin", "")))
            except ValueError as e:
                self._json(400, {"error": str(e)})
                return
            self._json(200, {"ok": True})
            return

        if path == "/api/device/revoke":
            s = self._require_auth(True)
            if not s:
                return
            if not s.is_admin or not is_loopback_source(self.client_address[0]):
                self._json(403, {"error": "Manajemen perangkat hanya dapat dilakukan dari localhost PC dengan PIN utama."})
                return
            try:
                data = self._json_body()
                peer = str(data.get("peer_id", ""))[:64]
            except Exception:
                self._json(400, {"error": "Data tidak valid."})
                return
            if not peer or peer == s.peer_id:
                self._json(400, {"error": "Perangkat aktif ini tidak dapat dicabut dari sesinya sendiri."})
                return
            revoke_device(peer)
            self.app_state.sessions.delete_peer(peer)
            self._json(200, {"ok": True, "peer_id": peer})
            return

        if path == "/api/local/device/action":
            s = self._require_auth(True)
            if not s:
                return
            if not s.is_admin or not is_loopback_source(self.client_address[0]):
                self._json(403, {"error": "Manajemen perangkat hanya tersedia dari http://localhost atau http://127.0.0.1 pada PC server."})
                return
            try:
                data = self._json_body()
                peer = str(data.get("peer_id", ""))[:64]
                action = str(data.get("action", "")).strip().lower()
            except Exception:
                self._json(400, {"error": "Data perangkat tidak valid."})
                return
            if not peer or peer == s.peer_id:
                self._json(400, {"error": "Perangkat localhost yang sedang dipakai tidak dapat diubah dari sesi ini."})
                return
            if not get_device(peer):
                self._json(404, {"error": "Perangkat tidak ditemukan."})
                return
            if action == "block":
                block_device(peer); self.app_state.sessions.delete_peer(peer)
            elif action == "unblock":
                unblock_device(peer)
            elif action == "revoke":
                revoke_device(peer); self.app_state.sessions.delete_peer(peer)
            elif action == "restore":
                restore_device(peer)
            elif action == "reset_pin":
                reset_device_pin(peer); self.app_state.sessions.delete_peer(peer)
            elif action == "delete":
                delete_registered_device(peer); self.app_state.sessions.delete_peer(peer)
            else:
                self._json(400, {"error": "Aksi perangkat tidak dikenal."})
                return
            self._json(200, {"ok": True, "peer_id": peer, "action": action})
            return

        if path == "/api/messages/clear":
            s = self._require_auth(True)
            if not s:
                return
            try:
                data = self._json_body()
                room = "public" if str(data.get("room", "private")) == "public" else "private"
                partner = str(data.get("partner", "__pc__"))[:64] if room == "private" else None
            except Exception:
                self._json(400, {"error": "Data pembersihan tidak valid."})
                return
            local_admin = bool(s.is_admin and is_local_machine_source(self.client_address[0]))
            ids = clear_room_messages(s.peer_id, room, partner, clear_public_all=local_admin)
            for mid in ids:
                self.app_state.control_queue.put(("close_popup", int(mid)))
            self._json(200, {"ok": True, "count": len(ids), "room": room, "public_all": bool(room == "public" and local_admin)})
            return

        if path == "/api/pairing/create":
            s = self._require_auth(True)
            if not s:
                return
            if not s.is_admin or not is_loopback_source(self.client_address[0]):
                self._json(403, {"error": "Pairing perangkat baru hanya dapat dibuat dari localhost PC dengan PIN utama."})
                return
            try:
                data = self._json_body()
                pair = create_pairing(s.peer_id, int(data.get("ttl", self.app_state.cfg.get("pairing_ttl_seconds", 600))))
                port = int(self.app_state.cfg.get("port", DEFAULT_PORT))
                url = f"http://{local_ip()}:{port}/?pair={pair['token']}"
                svg = qr_svg_v5_l(url)
            except Exception as e:
                self._json(500, {"error": f"Gagal membuat pairing: {e}"})
                return
            self._json(200, {"ok": True, "url": url, "code": pair["code"], "expires_at": pair["expires_at"], "expires_in": pair["expires_in"], "qr_svg": svg})
            return

        if path == "/api/pairing/cancel":
            s = self._require_auth(True)
            if not s:
                return
            if not s.is_admin or not is_loopback_source(self.client_address[0]):
                self._json(403, {"error": "Pairing hanya dapat dibatalkan dari localhost PC dengan PIN utama."})
                return
            count = cancel_active_pairing(s.peer_id)
            self._json(200, {"ok": True, "canceled": count})
            return

        if path == "/api/message/ack":
            s = self._require_auth(True)
            if not s:
                return
            try:
                data = self._json_body()
                mid = int(data.get("message_id", 0))
                stage = "opened" if str(data.get("stage", "opened")) == "opened" else "delivered"
            except Exception:
                self._json(400, {"error": "ID pesan tidak valid."})
                return
            if not acknowledge_message(s.peer_id, mid, stage):
                self._json(403, {"error": "Pesan tidak dapat dikonfirmasi oleh perangkat ini."})
                return
            self._json(200, {"ok": True})
            return

        if path == "/api/popup/close":
            s = self._require_auth(True)
            if not s:
                return
            try:
                data = self._json_body()
                mid = int(data.get("message_id", 0))
            except Exception:
                self._json(400, {"error": "ID pesan tidak valid."})
                return
            row = get_message(mid)
            if not row or row["sender_peer_id"] != s.peer_id or row["target_peer_id"] != "__pc__":
                self._json(404, {"error": "Popup pesan tidak ditemukan."})
                return
            self.app_state.control_queue.put(("close_popup", mid))
            self._json(200, {"ok": True, "message_id": mid})
            return

        if path == "/api/message/delete":
            s = self._require_auth(True)
            if not s:
                return
            try:
                data = self._json_body()
                mid = int(data.get("message_id", 0))
            except Exception:
                self._json(400, {"error": "ID pesan tidak valid."})
                return
            row = get_message(mid)
            if not row or row["sender_peer_id"] != s.peer_id:
                self._json(403, {"error": "Anda hanya dapat menghapus pesan yang dikirim dari perangkat ini."})
                return
            soft_delete_message(mid)
            if row["target_peer_id"] == "__pc__" or row["scope"] == "public":
                self.app_state.control_queue.put(("close_popup", mid))
            self._json(200, {"ok": True, "message_id": mid})
            return

        if path == "/api/send":
            s = self._require_auth(True)
            if not s:
                return
            max_upload = int(self.app_state.cfg.get("max_upload_mb", 50)) * 1024 * 1024
            try:
                body = self._read_body(max_upload + MAX_BODY_OVERHEAD)
                fields, file_info = self._parse_multipart(body)
            except OverflowError:
                self._json(413, {"error": f"File/payload melebihi batas {self.app_state.cfg.get('max_upload_mb', 50)} MB."})
                return
            except Exception as e:
                self._json(400, {"error": f"Payload tidak valid: {e}"})
                return
            text = str(fields.get("text", ""))[:10000].strip()
            scope = "public" if fields.get("scope", "private") == "public" else "private"
            target_peer = "__public__" if scope == "public" else str(fields.get("target_peer_id", "__pc__"))[:64]
            if scope == "private" and target_peer != "__pc__":
                target = get_device(target_peer)
                if not target or bool(target["revoked"]) or ("blocked" in set(target.keys()) and bool(target["blocked"])):
                    self._json(404, {"error": "Perangkat tujuan tidak tersedia atau sedang diblokir."})
                    return
                if target_peer == s.peer_id:
                    self._json(400, {"error": "Tidak dapat mengirim private ke perangkat yang sama."})
                    return
            stored_path = name = mime = None
            size = 0
            if file_info is not None:
                orig_name, data, _client_mime = file_info
                if len(data) > max_upload:
                    self._json(413, {"error": f"File melebihi batas {self.app_state.cfg.get('max_upload_mb', 50)} MB."})
                    return
                ok, why = file_allowed(self.app_state.cfg, orig_name, data)
                if not ok:
                    self._json(415, {"error": why})
                    return
                stored_path, name, size, mime = save_received_bytes(self.app_state.cfg, orig_name, data)
            if not text and not stored_path:
                self._json(400, {"error": "Pesan kosong."})
                return
            mode = fields.get("notify_mode", "popup")
            if mode not in {"popup", "windows", "toast", "both", "windows_toast", "silent"}:
                mode = "popup"
            try:
                duration = max(0, min(int(fields.get("duration", "15")), 3600))
            except Exception:
                duration = int(self.app_state.cfg.get("popup_default_duration", 15))
            sound = fields.get("sound", "default")
            if sound not in {"default", "chime", "double", "soft", "alert", "asterisk", "exclamation", "beep", "none"}:
                sound = "default"
            reply_to_id = None
            try:
                if str(fields.get("reply_to_id", "")).strip():
                    reply_to_id = int(fields.get("reply_to_id", "0"))
            except Exception:
                reply_to_id = None
            if reply_to_id:
                parent = get_message(reply_to_id)
                if not parent or bool(parent["deleted"]):
                    reply_to_id = None
                elif str(parent["scope"]) != scope:
                    # Never leak a quoted private message into the public room (or vice versa).
                    reply_to_id = None
                elif scope == "private":
                    participants = {str(parent["sender_peer_id"]), str(parent["target_peer_id"])}
                    if s.peer_id not in participants or target_peer not in participants:
                        reply_to_id = None
            b = lambda k, default=True: fields.get(k, "1" if default else "0") in {"1", "true", "yes", "on"}
            pc_receives = scope == "public" or target_peer == "__pc__"
            mid = insert_message(
                peer_id=s.peer_id,
                direction="to_pc",
                sender=s.device_name,
                text=text,
                file_path=stored_path,
                file_name=name,
                mime=mime,
                file_size=size,
                notify_mode=mode,
                duration=duration,
                allow_close=b("allow_close"),
                allow_reply=b("allow_reply"),
                allow_copy=b("allow_copy"),
                sound=sound,
                desktop_delivered=1 if (not pc_receives or mode == "silent") else 0,
                scope=scope,
                sender_peer_id=s.peer_id,
                target_peer_id=target_peer,
                reply_to_id=reply_to_id,
                delivered_at=now_iso() if pc_receives else None,
            )
            if pc_receives and mode != "silent":
                self.app_state.popup_queue.put(mid)
            row = get_message(mid)
            self._json(200, {"ok": True, "message": row_to_public(row) if row else {"id": mid}})
            return

        self._json(404, {"error": "Not found"})


class PopupManager:
    def __init__(self, app: AppState):
        self.app = app
        self.root = None
        self.tk = None
        self.ttk = None
        self.filedialog = None
        self.messagebox = None
        self.scrolledtext = None
        self._balloon_ids = 1000
        self.active_popups: Dict[int, Any] = {}
        self._after_jobs: Dict[int, list] = {}
        self._tray_nid = None
        self._tray_proc = None
        self._tray_old_proc = None
        self._tray_message = 0x8000 + 20

    def start(self) -> None:
        try:
            import tkinter as tk
            from tkinter import ttk, filedialog, messagebox
            from tkinter.scrolledtext import ScrolledText
            self.tk, self.ttk, self.filedialog, self.messagebox, self.scrolledtext = tk, ttk, filedialog, messagebox, ScrolledText
            self.root = tk.Tk()
            self.root.withdraw()
            self.root.title(APP_TITLE)
            try:
                self._setup_tray()
            except Exception as e:
                log(f"System tray tidak tersedia: {e}")
            self.root.after(120, self._pump)
            self.root.mainloop()
            self._remove_tray()
        except Exception as e:
            log(f"GUI tidak tersedia: {e}. Server tetap aktif tanpa popup native.")
            while not self.app.shutdown_event.wait(1):
                try:
                    mid = self.app.popup_queue.get_nowait()
                    mark_desktop_delivered(mid)
                except queue.Empty:
                    pass
                try:
                    self.app.control_queue.get_nowait()
                except queue.Empty:
                    pass

    def _pump(self) -> None:
        try:
            while True:
                mid = self.app.popup_queue.get_nowait()
                row = get_message(mid)
                if row and not bool(row["deleted"]):
                    try:
                        self.show_message(row)
                    except Exception:
                        log("Gagal menampilkan popup:\n" + traceback.format_exc())
                    finally:
                        mark_desktop_delivered(mid)
        except queue.Empty:
            pass
        try:
            while True:
                action, mid = self.app.control_queue.get_nowait()
                if action == "close_popup":
                    self.close_popup(mid)
        except queue.Empty:
            pass
        if self.root and not self.app.shutdown_event.is_set():
            self.root.after(120, self._pump)

    def _setup_tray(self) -> None:
        if os.name != "nt" or not self.root:
            return
        from ctypes import wintypes

        class NOTIFYICONDATAW(ctypes.Structure):
            _fields_ = [
                ("cbSize", wintypes.DWORD), ("hWnd", wintypes.HWND), ("uID", wintypes.UINT),
                ("uFlags", wintypes.UINT), ("uCallbackMessage", wintypes.UINT), ("hIcon", wintypes.HICON),
                ("szTip", wintypes.WCHAR * 128), ("dwState", wintypes.DWORD), ("dwStateMask", wintypes.DWORD),
                ("szInfo", wintypes.WCHAR * 256), ("uTimeoutOrVersion", wintypes.UINT),
                ("szInfoTitle", wintypes.WCHAR * 64), ("dwInfoFlags", wintypes.DWORD),
                ("guidItem", ctypes.c_byte * 16), ("hBalloonIcon", wintypes.HICON),
            ]

        shell = ctypes.windll.shell32
        user32 = ctypes.windll.user32
        hwnd = self.root.winfo_id()
        nid = NOTIFYICONDATAW()
        nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        nid.hWnd = hwnd
        nid.uID = 77
        nid.uFlags = 0x1 | 0x2 | 0x4  # NIF_MESSAGE | NIF_ICON | NIF_TIP
        nid.uCallbackMessage = self._tray_message
        nid.hIcon = user32.LoadIconW(None, 32516)
        nid.szTip = f"{APP_TITLE} v{VERSION}"[:127]
        if not shell.Shell_NotifyIconW(0, ctypes.byref(nid)):
            raise RuntimeError("Shell_NotifyIcon gagal")
        self._tray_nid = nid

        WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
        get_proc = getattr(user32, "GetWindowLongPtrW", user32.GetWindowLongW)
        set_proc = getattr(user32, "SetWindowLongPtrW", user32.SetWindowLongW)
        get_proc.argtypes = [wintypes.HWND, ctypes.c_int]
        get_proc.restype = ctypes.c_void_p
        set_proc.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_void_p]
        set_proc.restype = ctypes.c_void_p
        user32.CallWindowProcW.argtypes = [ctypes.c_void_p, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        user32.CallWindowProcW.restype = ctypes.c_ssize_t
        old_proc = get_proc(hwnd, -4)
        self._tray_old_proc = old_proc

        @WNDPROC
        def wndproc(hWnd, msg, wParam, lParam):
            if msg == self._tray_message:
                event = int(lParam) & 0xFFFF
                if event in (0x0205, 0x0203, 0x007B):  # right-up, left double-click, context menu
                    try:
                        self.root.after(0, self._show_tray_menu)
                    except Exception:
                        pass
                    return 0
            return user32.CallWindowProcW(self._tray_old_proc, hWnd, msg, wParam, lParam)

        self._tray_proc = wndproc
        set_proc(hwnd, -4, ctypes.cast(wndproc, ctypes.c_void_p).value)

    def _remove_tray(self) -> None:
        if os.name != "nt" or not self._tray_nid:
            return
        try:
            ctypes.windll.shell32.Shell_NotifyIconW(2, ctypes.byref(self._tray_nid))
        except Exception:
            pass
        self._tray_nid = None

    def _show_tray_menu(self) -> None:
        if not self.root:
            return
        tk = self.tk
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Buka WebApp", command=lambda: webbrowser.open(f"http://127.0.0.1:{int(self.app.cfg.get('port', DEFAULT_PORT))}"))
        menu.add_command(label="Buka folder file", command=lambda: self.open_folder(str(received_files_dir(self.app.cfg))))
        menu.add_command(label="Salin URL LAN", command=self._copy_lan_url)
        menu.add_separator()
        menu.add_command(label=("Aktifkan notifikasi" if self.app.notifications_paused else "Jeda notifikasi"), command=self._toggle_notifications)
        menu.add_command(label="Status", command=self._show_tray_status)
        menu.add_separator()
        menu.add_command(label="Restart BASKA SEND", command=self._restart_from_tray)
        menu.add_command(label="Keluar", command=self._exit_from_tray)
        try:
            menu.tk_popup(self.root.winfo_pointerx(), self.root.winfo_pointery())
        finally:
            try:
                menu.grab_release()
            except Exception:
                pass

    def _copy_lan_url(self) -> None:
        url = f"http://{local_ip()}:{int(self.app.cfg.get('port', DEFAULT_PORT))}"
        try:
            self.root.clipboard_clear(); self.root.clipboard_append(url); self.root.update()
        except Exception:
            pass

    def _toggle_notifications(self) -> None:
        self.app.notifications_paused = not self.app.notifications_paused
        state = "dijeda" if self.app.notifications_paused else "diaktifkan"
        try:
            self._windows_balloon(APP_TITLE, f"Notifikasi {state}.")
        except Exception:
            pass

    def _show_tray_status(self) -> None:
        text = (
            f"{APP_TITLE} v{VERSION}\n"
            f"URL LAN: http://{local_ip()}:{int(self.app.cfg.get('port', DEFAULT_PORT))}\n"
            f"File masuk: {received_files_dir(self.app.cfg)}\n"
            f"Notifikasi: {'DIJEDA' if self.app.notifications_paused else 'AKTIF'}"
        )
        try:
            self.messagebox.showinfo(APP_TITLE, text, parent=self.root)
        except Exception:
            pass

    def _exit_from_tray(self) -> None:
        self.app.shutdown_event.set()
        self._remove_tray()
        if self.app.httpd:
            threading.Thread(target=self.app.httpd.shutdown, daemon=True).start()
        try:
            self.root.after(100, self.root.destroy)
        except Exception:
            pass

    def _restart_from_tray(self) -> None:
        try:
            script = str(Path(__file__).resolve())
            py = Path(sys.executable)
            pyw = py.with_name("pythonw.exe") if os.name == "nt" else py
            exe = str(pyw if pyw.exists() else py)
            if os.name == "nt":
                cmd = f'timeout /t 2 /nobreak >nul & start "" "{exe}" "{script}" --run'
                subprocess.Popen(["cmd.exe", "/c", cmd], creationflags=0x00000008 | 0x00000200, close_fds=True)
            else:
                subprocess.Popen([exe, script, "--run"], start_new_session=True)
        except Exception as e:
            try:
                self.messagebox.showerror(APP_TITLE, f"Restart gagal:\n{e}")
            except Exception:
                pass
            return
        self._exit_from_tray()

    def play_sound(self, sound: str) -> None:
        if sound == "none" or os.name != "nt":
            return
        try:
            import winsound
            if sound == "chime":
                winsound.Beep(784, 90); winsound.Beep(1047, 130)
            elif sound == "double":
                winsound.Beep(880, 90); time.sleep(0.05); winsound.Beep(880, 90)
            elif sound == "soft":
                winsound.Beep(523, 70); winsound.Beep(659, 90)
            elif sound == "alert":
                winsound.Beep(988, 110); winsound.Beep(740, 110); winsound.Beep(988, 140)
            elif sound == "beep":
                winsound.Beep(880, 160)
            else:
                mapping = {"default": winsound.MB_OK, "asterisk": winsound.MB_ICONASTERISK, "exclamation": winsound.MB_ICONEXCLAMATION}
                winsound.MessageBeep(mapping.get(sound, winsound.MB_OK))
        except Exception:
            pass

    def _windows_balloon(self, title: str, text: str) -> None:
        if os.name != "nt" or not self.root:
            return
        try:
            from ctypes import wintypes

            class NOTIFYICONDATAW(ctypes.Structure):
                _fields_ = [
                    ("cbSize", wintypes.DWORD), ("hWnd", wintypes.HWND), ("uID", wintypes.UINT),
                    ("uFlags", wintypes.UINT), ("uCallbackMessage", wintypes.UINT), ("hIcon", wintypes.HICON),
                    ("szTip", wintypes.WCHAR * 128), ("dwState", wintypes.DWORD), ("dwStateMask", wintypes.DWORD),
                    ("szInfo", wintypes.WCHAR * 256), ("uTimeoutOrVersion", wintypes.UINT),
                    ("szInfoTitle", wintypes.WCHAR * 64), ("dwInfoFlags", wintypes.DWORD),
                    ("guidItem", ctypes.c_byte * 16), ("hBalloonIcon", wintypes.HICON),
                ]

            shell, user32 = ctypes.windll.shell32, ctypes.windll.user32
            NIM_ADD, NIM_MODIFY, NIM_DELETE = 0, 1, 2
            NIF_ICON, NIF_TIP, NIF_INFO, NIIF_INFO = 0x2, 0x4, 0x10, 0x1
            nid = NOTIFYICONDATAW()
            nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
            nid.hWnd = self.root.winfo_id()
            self._balloon_ids += 1
            nid.uID = self._balloon_ids
            nid.uFlags = NIF_ICON | NIF_TIP
            nid.hIcon = user32.LoadIconW(None, 32516)
            nid.szTip = APP_TITLE[:127]
            shell.Shell_NotifyIconW(NIM_ADD, ctypes.byref(nid))
            nid.uFlags = NIF_INFO
            nid.szInfoTitle = title[:63]
            nid.szInfo = text[:255]
            nid.dwInfoFlags = NIIF_INFO
            nid.uTimeoutOrVersion = 8000
            shell.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(nid))
            self.root.after(9000, lambda: shell.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(nid)))
        except Exception as e:
            log(f"Notifikasi Windows gagal: {e}")

    def _place_bottom_right(self, win, width: int, height: int) -> None:
        """Place a popup at the bottom-right while keeping it inside the usable screen area."""
        try:
            win.update_idletasks()
        except Exception:
            pass
        sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
        max_w = max(360, sw - 24)
        max_h = max(250, sh - 90)
        width = max(360, min(int(width), max_w))
        height = max(250, min(int(height), max_h))
        x = max(0, sw - width - 22)
        y = max(0, sh - height - 68)
        win.geometry(f"{width}x{height}+{x}+{y}")

    def _fit_popup_to_content(self, win, preferred_width: int, preferred_height: int) -> None:
        """Resize a popup compactly but never smaller than the controls it actually needs.

        Tk can keep a stale geometry request for one idle cycle after reply widgets are
        added/removed.  Updating twice avoids the lower action row being pushed outside
        the visible client area after closing reply mode.
        """
        try:
            win.update_idletasks()
            # A second idle update is deliberate: geometry propagation after pack_forget()
            # can otherwise lag by one cycle on older Windows/Tk builds.
            win.after_idle(lambda: None)
            win.update_idletasks()
            req_w = max(1, int(win.winfo_reqwidth()))
            req_h = max(1, int(win.winfo_reqheight()))
        except Exception:
            req_w, req_h = preferred_width, preferred_height
        # Keep a small safety margin around the requested client area.
        target_w = max(int(preferred_width), req_w + 4)
        target_h = max(int(preferred_height), req_h + 6)
        self._place_bottom_right(win, target_w, target_h)

    def _register_popup(self, mid: int, win) -> None:
        old = self.active_popups.get(mid)
        if old and old.winfo_exists():
            try:
                old.destroy()
            except Exception:
                pass
        self.active_popups[mid] = win
        self._after_jobs[mid] = []

        def gone(evt=None):
            # <Destroy> on a Toplevel can also be delivered when one of its child
            # widgets is destroyed.  Only unregister the popup when the Toplevel
            # itself is actually being destroyed.  Without this guard, closing the
            # inline reply panel made the popup disappear from active_popups while
            # the window was still visible, breaking X, timer and remote-close.
            if evt is not None and getattr(evt, "widget", None) is not win:
                return
            if self.active_popups.get(mid) is win:
                self.active_popups.pop(mid, None)
            jobs = self._after_jobs.pop(mid, [])
            if self.root:
                for job in list(jobs):
                    try:
                        self.root.after_cancel(job)
                    except Exception:
                        pass

        win.bind("<Destroy>", gone, add="+")

    def close_popup(self, mid: int) -> None:
        win = self.active_popups.pop(int(mid), None)
        jobs = self._after_jobs.pop(int(mid), [])
        if self.root:
            for job in jobs:
                try:
                    self.root.after_cancel(job)
                except Exception:
                    pass
        if win:
            try:
                if win.winfo_exists():
                    win.destroy()
            except Exception:
                pass

    def _cancel_countdown(self, mid: int) -> None:
        jobs = self._after_jobs.get(int(mid), [])
        if self.root:
            for job in list(jobs):
                try:
                    self.root.after_cancel(job)
                except Exception:
                    pass
        self._after_jobs[int(mid)] = []

    def _countdown(self, mid: int, win, label, duration: int) -> None:
        """Start exactly one countdown job for a popup.

        Re-starting the timer (for example after closing reply mode) first cancels the
        old job. This prevents multiple timers racing each other or a stale timer from
        closing a popup unexpectedly.
        """
        self._cancel_countdown(mid)
        duration = max(0, int(duration or 0))
        if duration <= 0:
            try:
                label.configure(text="Tetap terbuka sampai ditutup")
            except Exception:
                pass
            return
        deadline = time.monotonic() + duration

        def tick():
            try:
                if not win.winfo_exists():
                    self._after_jobs[int(mid)] = []
                    return
            except Exception:
                self._after_jobs[int(mid)] = []
                return
            left = max(0, int(deadline - time.monotonic() + .999))
            try:
                label.configure(text=f"Menutup otomatis dalam {left} detik")
            except Exception:
                pass
            if left <= 0:
                self._after_jobs[int(mid)] = []
                self.close_popup(mid)
                return
            try:
                job = self.root.after(250, tick)
                self._after_jobs[int(mid)] = [job]
            except Exception:
                self._after_jobs[int(mid)] = []

        tick()

    def _copy_chunks(self, text: str) -> Tuple[str, list]:
        """Return logical copy units. Blank-line separated text is treated as paragraphs;
        otherwise each non-empty explicit line becomes its own copy unit.
        """
        value = str(text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
        if not value:
            return "baris", []
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", value) if p.strip()]
        if len(paragraphs) > 1:
            return "paragraf", paragraphs
        lines = [line.strip() for line in value.split("\n") if line.strip()]
        return "baris", (lines or [value])

    def _copy_success_toast(self, host_win, message: str, ok: bool = True) -> None:
        """Small non-blocking toast so the user knows clipboard copy succeeded."""
        if not self.root:
            return
        try:
            tk = self.tk
            parent = host_win if host_win is not None else self.root
            if hasattr(parent, "winfo_exists") and not parent.winfo_exists():
                parent = self.root
            toast = tk.Toplevel(parent)
            toast.overrideredirect(True)
            toast.attributes("-topmost", True)
            bg = "#166534" if ok else "#991b1b"
            fg = "#ffffff"
            frame = tk.Frame(toast, bg=bg, highlightbackground="#ffffff", highlightthickness=1)
            frame.pack(fill="both", expand=True)
            tk.Label(frame, text=message, bg=bg, fg=fg, font=("Segoe UI", 9, "bold"), padx=14, pady=9).pack()
            toast.update_idletasks()
            tw, th = toast.winfo_reqwidth(), toast.winfo_reqheight()
            try:
                px, py = parent.winfo_rootx(), parent.winfo_rooty()
                pw, ph = parent.winfo_width(), parent.winfo_height()
                x = max(4, px + pw - tw - 18)
                y = max(4, py + ph - th - 18)
            except Exception:
                sw, sh = toast.winfo_screenwidth(), toast.winfo_screenheight()
                x, y = max(4, sw - tw - 24), max(4, sh - th - 70)
            toast.geometry(f"+{x}+{y}")
            toast.after(1700, lambda: toast.destroy() if toast.winfo_exists() else None)
        except Exception:
            pass

    def _build_copy_section_modern(self, parent, text: str, host_win) -> None:
        mode, chunks = self._copy_chunks(text)
        if not chunks:
            return
        tk = self.tk
        try:
            host_win._copy_visual_modern = []
        except Exception:
            pass
        outer = tk.Frame(parent, bg="#171f2d")
        outer.pack(fill="x", padx=10, pady=(0, 10))
        tk.Label(outer, text=f"Salin per {mode}", fg="#8fb0ff", bg="#171f2d", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(2, 5))
        height = min(82, max(34, len(chunks) * 31))
        wrap = tk.Frame(outer, bg="#171f2d")
        wrap.pack(fill="x")
        canvas = tk.Canvas(wrap, height=height, bg="#171f2d", highlightthickness=0, borderwidth=0)
        scroll = tk.Scrollbar(wrap, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg="#171f2d")
        inner_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="x", expand=True)
        if len(chunks) * 31 > height:
            scroll.pack(side="right", fill="y")

        def sync(_e=None):
            try:
                canvas.configure(scrollregion=canvas.bbox("all"))
                canvas.itemconfigure(inner_id, width=canvas.winfo_width())
            except Exception:
                pass

        inner.bind("<Configure>", sync)
        canvas.bind("<Configure>", sync)
        for i, chunk in enumerate(chunks, 1):
            r = tk.Frame(inner, bg="#202b3c", highlightbackground="#2d3a50", highlightthickness=1)
            r.pack(fill="x", pady=(0, 5))
            txt_label = tk.Label(r, text=chunk, fg="#e7ecf7", bg="#202b3c", anchor="w", justify="left", wraplength=410, font=("Segoe UI", 9), padx=8, pady=7)
            txt_label.pack(side="left", fill="x", expand=True)
            label = f"{mode.capitalize()} {i}"
            copy_btn = tk.Button(r, text="Copy", bg="#1a2435", fg="#e7ecf7", activebackground="#315da8", activeforeground="white", relief="flat", padx=10, pady=5)
            copy_btn.pack(side="right", padx=6, pady=5)
            def do_copy(c=chunk, lab=label, row_frame=r, text_widget=txt_label, button=copy_btn):
                if self.copy_text(c, host_win, lab):
                    row_frame.configure(bg="#173c2b", highlightbackground="#22c55e")
                    text_widget.configure(bg="#173c2b", fg="#9df0bd")
                    button.configure(text="Tersalin ✓", bg="#166534", fg="#ffffff")
            copy_btn.configure(command=do_copy)
            try:
                host_win._copy_visual_modern.append((r, txt_label, copy_btn))
            except Exception:
                pass
        sync()

    def _build_copy_section_windows(self, parent, text: str, host_win) -> None:
        mode, chunks = self._copy_chunks(text)
        if not chunks:
            return
        tk, ttk = self.tk, self.ttk
        try:
            host_win._copy_visual_windows = []
        except Exception:
            pass
        section = ttk.LabelFrame(parent, text=f"Salin per {mode}", padding=6)
        section.pack(fill="x", pady=(8, 0))
        height = min(72, max(32, len(chunks) * 30))
        holder = ttk.Frame(section)
        holder.pack(fill="x")
        try:
            bg = str(self.ttk.Style().lookup("TFrame", "background") or self.root.cget("background"))
        except Exception:
            bg = "#f0f0f0"
        canvas = tk.Canvas(holder, height=height, highlightthickness=0, borderwidth=0, bg=bg)
        scroll = ttk.Scrollbar(holder, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas)
        inner_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="x", expand=True)
        if len(chunks) * 30 > height:
            scroll.pack(side="right", fill="y")

        def sync(_e=None):
            try:
                canvas.configure(scrollregion=canvas.bbox("all"))
                canvas.itemconfigure(inner_id, width=canvas.winfo_width())
            except Exception:
                pass

        inner.bind("<Configure>", sync)
        canvas.bind("<Configure>", sync)
        for i, chunk in enumerate(chunks, 1):
            r = ttk.Frame(inner)
            r.pack(fill="x", pady=(0, 4))
            txt_label = ttk.Label(r, text=chunk, anchor="w", justify="left", wraplength=390)
            txt_label.pack(side="left", fill="x", expand=True, padx=(2, 8))
            label = f"{mode.capitalize()} {i}"
            copy_btn = ttk.Button(r, text="Copy")
            copy_btn.pack(side="right")
            def do_copy(c=chunk, lab=label, text_widget=txt_label, button=copy_btn):
                if self.copy_text(c, host_win, lab):
                    try:
                        text_widget.configure(foreground="#16803a")
                    except Exception:
                        pass
                    button.configure(text="Tersalin ✓")
            copy_btn.configure(command=do_copy)
            try:
                host_win._copy_visual_windows.append((txt_label, copy_btn))
            except Exception:
                pass
        sync()

    def show_message(self, row: sqlite3.Row) -> None:
        if self.app.notifications_paused:
            return
        mode = row["notify_mode"]
        mark_message_opened(int(row["id"]))
        self.play_sound(row["sound"])
        summary = row["text"].strip() or (f"File: {row['file_name']}" if row["file_name"] else "Pesan baru")
        title = f"Pesan publik dari {row['sender']}" if row["scope"] == "public" else f"Pesan dari {row['sender']}"
        if mode in {"toast", "both", "windows_toast"}:
            self._windows_balloon(title, summary)
        if mode in {"silent", "toast"}:
            return
        if mode in {"windows", "windows_toast"}:
            self._show_windows_dialog(row)
        else:
            self._show_modern_popup(row)

    def _file_actions_modern(self, parent, row: sqlite3.Row, bg: str) -> None:
        tk = self.tk
        bar = tk.Frame(parent, bg=bg)
        bar.pack(fill="x", padx=18, pady=(2, 6))
        tk.Label(bar, text=f"File: {row['file_name']}  ({self._human_bytes(row['file_size'])})", fg="#cbd4e6", bg=bg, anchor="w", font=("Segoe UI", 9)).pack(fill="x", pady=(0, 5))
        btns = tk.Frame(bar, bg=bg)
        btns.pack(fill="x")

        def add(text, command):
            tk.Button(btns, text=text, command=command, bg="#1a2435", fg="#e7ecf7", activebackground="#25314a", activeforeground="white", relief="flat", padx=10, pady=5).pack(side="left", padx=(0, 6))

        if Path(row["file_name"] or "").suffix.lower() in PREVIEWABLE_EXTENSIONS:
            add("Preview", lambda p=row["file_path"]: self.preview_file(p, parent))
        add("Buka file", lambda p=row["file_path"]: self.open_file(p))
        add("Buka folder", lambda p=row["file_path"]: self.open_folder(p))
        add("Detail", lambda r=dict(row): self.show_file_details(r, parent))

    def _file_actions_windows(self, parent, row: sqlite3.Row) -> None:
        ttk = self.ttk
        fbar = ttk.Frame(parent)
        fbar.pack(fill="x", pady=(8, 0))
        ttk.Label(fbar, text=f"File: {row['file_name']} ({self._human_bytes(row['file_size'])})").pack(anchor="w", pady=(0, 5))
        btns = ttk.Frame(fbar)
        btns.pack(fill="x")
        if Path(row["file_name"] or "").suffix.lower() in PREVIEWABLE_EXTENSIONS:
            ttk.Button(btns, text="Preview", command=lambda p=row["file_path"]: self.preview_file(p, parent)).pack(side="left", padx=(0, 5))
        ttk.Button(btns, text="Buka file", command=lambda p=row["file_path"]: self.open_file(p)).pack(side="left", padx=(0, 5))
        ttk.Button(btns, text="Buka folder", command=lambda p=row["file_path"]: self.open_folder(p)).pack(side="left", padx=(0, 5))
        ttk.Button(btns, text="Detail", command=lambda r=dict(row): self.show_file_details(r, parent)).pack(side="left")

    def _show_modern_popup(self, row: sqlite3.Row) -> None:
        tk = self.tk
        mid = int(row["id"])
        win = tk.Toplevel(self.root)
        win.withdraw()
        win.title(f"{APP_TITLE} - {row['sender']}")
        win.attributes("-topmost", True)
        win.configure(bg="#101722")
        win.minsize(400, 280)
        win._base_popup_size = (500, 375)
        self._register_popup(mid, win)
        # X/Alt+F4 selalu berfungsi. allow_close hanya mengatur tombol Tutup di body.
        win.protocol("WM_DELETE_WINDOW", lambda: self.close_popup(mid))

        top = tk.Frame(win, bg="#101722")
        top.pack(fill="x", padx=14, pady=(12, 6))
        tk.Label(top, text="BASKA SEND • RUANG UMUM" if row["scope"] == "public" else "BASKA SEND • PRIVATE", fg="#79a0ff", bg="#101722", font=("Segoe UI", 8, "bold")).pack(anchor="w")
        tk.Label(top, text=f"Pesan dari {row['sender']}", fg="#f5f7fb", bg="#101722", font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(3, 0))
        tk.Label(top, text=format_datetime_id(row["created_at"]), fg="#8994aa", bg="#101722", font=("Segoe UI", 8)).pack(anchor="w", pady=(1, 0))

        body = tk.Frame(win, bg="#171f2d", highlightbackground="#293445", highlightthickness=1)
        body.pack(fill="both", expand=True, padx=14, pady=6)
        if row["reply_to_id"]:
            q = _reply_preview(int(row["reply_to_id"]))
            if q:
                qtxt = (q.get("text") or q.get("file_name") or "Pesan")[:180]
                qbox = tk.Frame(body, bg="#202b3c", highlightbackground="#4c7dff", highlightthickness=1)
                qbox.pack(fill="x", padx=8, pady=(7, 0))
                tk.Label(qbox, text=f"Membalas {q.get('sender','Pesan')}", fg="#8fb0ff", bg="#202b3c", font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=8, pady=(5, 1))
                tk.Label(qbox, text=qtxt, fg="#cbd4e6", bg="#202b3c", font=("Segoe UI", 8), anchor="w", justify="left", wraplength=450).pack(fill="x", padx=8, pady=(0, 5))
        text_box = self.scrolledtext(body, wrap="word", height=4, bg="#171f2d", fg="#f0f3f8", insertbackground="white", relief="flat", font=("Segoe UI", 9), padx=8, pady=6)
        text_box.pack(fill="both", expand=True)
        text_box.insert("1.0", row["text"] or "")
        text_box.configure(state="disabled")
        if row["allow_copy"] and row["text"]:
            self._build_copy_section_modern(body, row["text"], win)

        if row["file_name"]:
            self._file_actions_modern(win, row, "#101722")

        reply_holder = tk.Frame(win, bg="#101722")
        countdown = tk.Label(win, text="", fg="#8e9bb0", bg="#101722", font=("Segoe UI", 8))
        countdown.pack(anchor="w", padx=14, pady=(2, 0))
        reply_holder._reply_before = countdown
        reply_holder._reply_style = "modern"

        actions = tk.Frame(win, bg="#101722")
        actions.pack(fill="x", padx=14, pady=(5, 12))
        if row["allow_copy"] and row["text"]:
            copy_all_btn = tk.Button(actions, text="Copy semua", bg="#1a2435", fg="#e7ecf7", relief="flat", padx=11, pady=6)
            copy_all_btn.pack(side="left", padx=(0, 6))

            def copy_all_modern(t=row["text"], button=copy_all_btn):
                if self.copy_text(t, win, "Semua teks"):
                    button.configure(text="Semua tersalin ✓", bg="#166534", fg="#ffffff")
                    for row_frame, text_widget, row_button in getattr(win, "_copy_visual_modern", []):
                        try:
                            row_frame.configure(bg="#173c2b", highlightbackground="#22c55e")
                            text_widget.configure(bg="#173c2b", fg="#9df0bd")
                            row_button.configure(text="Tersalin ✓", bg="#166534", fg="#ffffff")
                        except Exception:
                            pass

            copy_all_btn.configure(command=copy_all_modern)
        if row["allow_reply"]:
            tk.Button(actions, text="Balas", command=lambda: self.show_inline_reply(reply_holder, dict(row), win, countdown, mid, False), bg="#4c7dff", fg="white", relief="flat", padx=14, pady=6).pack(side="left")
        if row["allow_close"]:
            tk.Button(actions, text="Tutup", command=lambda: self.close_popup(mid), bg="#202a3d", fg="#e7ecf7", relief="flat", padx=11, pady=6).pack(side="right")
        elif int(row["duration"] or 0) == 0:
            tk.Label(actions, text="Tutup dari WebApp atau tombol X", fg="#8e9bb0", bg="#101722", font=("Segoe UI", 8)).pack(side="right")

        self._countdown(mid, win, countdown, int(row["duration"] or 0))
        self._fit_popup_to_content(win, *win._base_popup_size)
        win.deiconify()
        win.lift()
        win.focus_force()

    def _show_windows_dialog(self, row: sqlite3.Row) -> None:
        tk, ttk = self.tk, self.ttk
        mid = int(row["id"])
        win = tk.Toplevel(self.root)
        win.withdraw()
        win.title(f"BASKA SEND - Pesan dari {row['sender']}")
        win.attributes("-topmost", True)
        win.resizable(True, True)
        win.minsize(400, 270)
        win._base_popup_size = (500, 365)
        self._register_popup(mid, win)
        # Tombol X/Alt+F4 selalu harus benar-benar menutup jendela. Opsi allow_close
        # hanya mengatur keberadaan tombol "Tutup" di dalam isi popup.
        win.protocol("WM_DELETE_WINDOW", lambda: self.close_popup(mid))

        outer = ttk.Frame(win, padding=(11, 9, 11, 9))
        outer.pack(fill="both", expand=True)

        # Footer dipack lebih dulu di sisi bawah. Dengan demikian tombol aksi, timer,
        # file-detail dan composer balasan tetap terlihat walau tinggi layar terbatas.
        footer = ttk.Frame(outer)
        footer.pack(side="bottom", fill="x")

        if row["file_name"]:
            self._file_actions_windows(footer, row)

        reply_holder = ttk.Frame(footer)
        countdown = ttk.Label(footer, text="", font=("Segoe UI", 8))
        countdown.pack(anchor="w", pady=(5, 0))
        reply_holder._reply_before = countdown
        reply_holder._reply_style = "windows"

        ttk.Separator(footer).pack(fill="x", pady=(6, 5))
        buttons = ttk.Frame(footer)
        buttons.pack(fill="x")
        if row["allow_copy"] and row["text"]:
            copy_all_btn = ttk.Button(buttons, text="Copy semua")
            copy_all_btn.pack(side="left", padx=(0, 5))

            def copy_all_windows(t=row["text"], button=copy_all_btn):
                if self.copy_text(t, win, "Semua teks"):
                    button.configure(text="Semua tersalin ✓")
                    for text_widget, row_button in getattr(win, "_copy_visual_windows", []):
                        try:
                            text_widget.configure(foreground="#16803a")
                            row_button.configure(text="Tersalin ✓")
                        except Exception:
                            pass

            copy_all_btn.configure(command=copy_all_windows)
        if row["allow_reply"]:
            ttk.Button(
                buttons,
                text="Balas",
                command=lambda: self.show_inline_reply(reply_holder, dict(row), win, countdown, mid, True),
            ).pack(side="left")
        if row["allow_close"]:
            ttk.Button(buttons, text="Tutup", command=lambda: self.close_popup(mid)).pack(side="right")
        elif int(row["duration"] or 0) == 0:
            ttk.Label(buttons, text="Tutup dari WebApp atau tombol X", font=("Segoe UI", 8)).pack(side="right")

        # Area atas dapat discroll. Ini mencegah isi pesan/copy-per-baris mendorong
        # footer keluar dari jendela pada layar kecil atau saat pesan sangat panjang.
        content_wrap = ttk.Frame(outer)
        content_wrap.pack(side="top", fill="both", expand=True, pady=(0, 6))
        try:
            canvas_bg = str(ttk.Style().lookup("TFrame", "background") or self.root.cget("background"))
        except Exception:
            canvas_bg = "#f0f0f0"
        canvas = tk.Canvas(content_wrap, height=190, highlightthickness=0, borderwidth=0, bg=canvas_bg)
        vscroll = ttk.Scrollbar(content_wrap, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas)
        inner_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=vscroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        vscroll.pack(side="right", fill="y")

        def sync_content(_evt=None):
            try:
                canvas.configure(scrollregion=canvas.bbox("all"))
                canvas.itemconfigure(inner_id, width=max(1, canvas.winfo_width()))
                bbox = canvas.bbox("all")
                if bbox:
                    need_scroll = (bbox[3] - bbox[1]) > canvas.winfo_height() + 2
                    if need_scroll and not vscroll.winfo_ismapped():
                        vscroll.pack(side="right", fill="y")
                    elif not need_scroll and vscroll.winfo_ismapped():
                        vscroll.pack_forget()
            except Exception:
                pass

        inner.bind("<Configure>", sync_content)
        canvas.bind("<Configure>", sync_content)

        def wheel(evt):
            try:
                delta = int(-1 * (evt.delta / 120)) if getattr(evt, "delta", 0) else 0
                if delta:
                    canvas.yview_scroll(delta, "units")
            except Exception:
                pass
            return "break"

        canvas.bind("<MouseWheel>", wheel)
        inner.bind("<MouseWheel>", wheel)

        ttk.Label(inner, text=f"Pesan dari {row['sender']}", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        ttk.Label(
            inner,
            text=("Ruang Umum • " if row["scope"] == "public" else "Private • ") + format_datetime_id(row["created_at"]),
            font=("Segoe UI", 8),
        ).pack(anchor="w", pady=(1, 6))

        if row["reply_to_id"]:
            q = _reply_preview(int(row["reply_to_id"]))
            if q:
                qtxt = (q.get("text") or q.get("file_name") or "Pesan")[:180]
                qf = ttk.LabelFrame(inner, text=f"Membalas {q.get('sender','Pesan')}", padding=5)
                qf.pack(fill="x", pady=(0, 5))
                ttk.Label(qf, text=qtxt, wraplength=430, justify="left", font=("Segoe UI", 8)).pack(anchor="w")

        txt = tk.Text(inner, wrap="word", height=4, relief="sunken", borderwidth=1, font=("Segoe UI", 9), padx=6, pady=5)
        txt.pack(fill="x")
        txt.insert("1.0", row["text"] or "")
        txt.configure(state="disabled")

        if row["allow_copy"] and row["text"]:
            self._build_copy_section_windows(inner, row["text"], win)

        self._countdown(mid, win, countdown, int(row["duration"] or 0))
        self._fit_popup_to_content(win, *win._base_popup_size)
        sync_content()
        win.deiconify()
        win.lift()
        win.focus_force()

    def show_inline_reply(self, holder, row: Dict[str, Any], host_win, countdown_label, mid: int, windows_style: bool) -> None:
        """Open the inline reply composer inside the existing popup.

        The composer is shown/hidden without leaving stale geometry behind. While it is
        open the auto-close timer is paused; closing the composer starts a fresh timer
        using the message's configured duration.
        """
        self._cancel_countdown(mid)
        try:
            countdown_label.configure(text="Mode balas aktif • timer dijeda")
        except Exception:
            pass

        # Ensure the holder occupies space only while reply mode is active.
        if not holder.winfo_manager():
            before = getattr(holder, "_reply_before", None)
            try:
                if before is not None:
                    holder.pack(fill="x", padx=(0 if windows_style else 14), pady=(5, 0), before=before)
                else:
                    holder.pack(fill="x", pady=(5, 0))
            except Exception:
                holder.pack(fill="x", pady=(5, 0))

        for child in holder.winfo_children():
            try:
                child.destroy()
            except Exception:
                pass

        tk = self.tk
        selected = {"path": None}
        reply_history_widgets = []

        if windows_style:
            ttk = self.ttk
            frame = ttk.LabelFrame(holder, text=f"Balas ke {row['sender']}", padding=5)
            frame.pack(fill="x")
            history = ttk.Frame(frame)
            history.pack(fill="x")
            txt = tk.Text(frame, wrap="word", height=2, font=("Segoe UI", 9), padx=5, pady=4)
            txt.pack(fill="x", pady=(2, 3))
            status = ttk.Label(frame, text="Tidak ada file", font=("Segoe UI", 8))
            status.pack(anchor="w", pady=(0, 2))
            btns = ttk.Frame(frame)
            btns.pack(fill="x", pady=(2, 0))

            def add_reply_preview(message, file_name):
                label = ttk.Label(
                    history,
                    text=f"BASKA SEND: {message or '[file]'}" + (f" | File: {file_name}" if file_name else ""),
                    wraplength=430,
                    justify="left",
                    font=("Segoe UI", 8),
                )
                label.pack(anchor="e", pady=(0, 2))
                reply_history_widgets.append(label)
                while len(reply_history_widgets) > 2:
                    old = reply_history_widgets.pop(0)
                    try:
                        old.destroy()
                    except Exception:
                        pass

            choose_btn = ttk.Button(btns, text="Pilih File")
            choose_btn.pack(side="left", padx=(0, 5))
            close_reply_btn = ttk.Button(btns, text="Tutup Balasan")
            close_reply_btn.pack(side="left")
            send_btn = ttk.Button(btns, text="Kirim")
            send_btn.pack(side="right")
        else:
            frame = tk.Frame(holder, bg="#151d2a", highlightbackground="#293445", highlightthickness=1)
            frame.pack(fill="x")
            tk.Label(frame, text=f"Balas ke {row['sender']}", fg="#f5f7fb", bg="#151d2a", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=8, pady=(5, 2))
            history = tk.Frame(frame, bg="#151d2a")
            history.pack(fill="x", padx=8)
            txt = tk.Text(frame, wrap="word", height=2, bg="#101722", fg="#f0f3f8", insertbackground="white", relief="flat", font=("Segoe UI", 9), padx=6, pady=4)
            txt.pack(fill="x", padx=8, pady=(2, 3))
            status = tk.Label(frame, text="Tidak ada file", fg="#8e9bb0", bg="#151d2a", anchor="w", font=("Segoe UI", 8))
            status.pack(fill="x", padx=8)
            btns = tk.Frame(frame, bg="#151d2a")
            btns.pack(fill="x", padx=8, pady=(4, 6))

            def add_reply_preview(message, file_name):
                label = tk.Label(
                    history,
                    text=f"BASKA SEND: {message or '[file]'}" + (f" | File: {file_name}" if file_name else ""),
                    fg="#eef3ff",
                    bg="#2b54a8",
                    justify="left",
                    anchor="e",
                    wraplength=420,
                    font=("Segoe UI", 8),
                    padx=6,
                    pady=3,
                )
                label.pack(anchor="e", pady=(0, 2))
                reply_history_widgets.append(label)
                while len(reply_history_widgets) > 2:
                    old = reply_history_widgets.pop(0)
                    try:
                        old.destroy()
                    except Exception:
                        pass

            choose_btn = tk.Button(btns, text="Pilih File", bg="#1a2435", fg="#e7ecf7", relief="flat", padx=9, pady=4)
            choose_btn.pack(side="left", padx=(0, 5))
            close_reply_btn = tk.Button(btns, text="Tutup Balasan", bg="#202a3d", fg="#e7ecf7", relief="flat", padx=9, pady=4)
            close_reply_btn.pack(side="left")
            send_btn = tk.Button(btns, text="Kirim", bg="#4c7dff", fg="white", relief="flat", padx=12, pady=4)
            send_btn.pack(side="right")

        def choose():
            pattern = " ".join(f"*{x}" for x in self.app.cfg.get("allowed_extensions", DEFAULT_ALLOWED_EXTENSIONS))
            path = self.filedialog.askopenfilename(
                parent=host_win,
                title="Pilih file balasan",
                filetypes=[("File diizinkan", pattern), ("Semua file", "*.*")],
            )
            if path:
                selected["path"] = path
                status.configure(text=Path(path).name)

        def close_reply():
            # Cancel any reply-mode timer state, destroy controls, and remove the holder
            # completely so it cannot leave a blank area that hides lower controls.
            self._cancel_countdown(mid)
            for child in holder.winfo_children():
                try:
                    child.destroy()
                except Exception:
                    pass
            try:
                holder.pack_forget()
            except Exception:
                pass
            try:
                host_win.update_idletasks()
            except Exception:
                pass
            duration = int(row.get("duration") or 0)
            self._countdown(mid, host_win, countdown_label, duration)
            try:
                base_w, base_h = getattr(host_win, "_base_popup_size", (500, 360 if windows_style else 375))
                self._fit_popup_to_content(host_win, int(base_w), int(base_h))
            except Exception:
                pass
            return "break"

        def send_reply():
            message = txt.get("1.0", "end").strip()
            if not message and not selected["path"]:
                try:
                    status.configure(text="Tulis pesan atau pilih file terlebih dahulu")
                except Exception:
                    pass
                return
            try:
                send_btn.configure(state="disabled", text="Mengirim...")
                self.app.create_reply(
                    str(row.get("sender_peer_id") or row.get("peer_id")),
                    message,
                    selected["path"],
                    str(row.get("scope", "private")),
                    reply_to_id=int(row.get("id") or mid),
                )
                add_reply_preview(message, Path(selected["path"]).name if selected["path"] else None)
                txt.delete("1.0", "end")
                selected["path"] = None
                status.configure(text="Balasan terkirim")
            except Exception as e:
                self.messagebox.showerror(APP_TITLE, str(e), parent=host_win)
            finally:
                try:
                    send_btn.configure(state="normal", text="Kirim")
                except Exception:
                    pass
                try:
                    self._fit_popup_to_content(host_win, 500, 420 if windows_style else 430)
                except Exception:
                    pass

        choose_btn.configure(command=choose)
        close_reply_btn.configure(command=close_reply)
        send_btn.configure(command=send_reply)
        txt.bind("<Control-Return>", lambda _e: send_reply())
        txt.bind("<Escape>", lambda _e: close_reply())
        txt.focus_set()
        try:
            self._fit_popup_to_content(host_win, 500, 420 if windows_style else 430)
        except Exception:
            pass

    def _human_bytes(self, n: int) -> str:
        n = int(n or 0)
        units = ["B", "KB", "MB", "GB"]
        i = 0
        x = float(n)
        while x >= 1024 and i < len(units) - 1:
            x /= 1024.0
            i += 1
        return f"{x:.1f} {units[i]}" if i else f"{int(x)} B"

    def copy_text(self, text: str, host_win=None, label: str = "Teks") -> bool:
        try:
            value = str(text or "")
            if not value:
                self._copy_success_toast(host_win, "Tidak ada teks untuk disalin", ok=False)
                return False
            self.root.clipboard_clear()
            self.root.clipboard_append(value)
            self.root.update()
            self._copy_success_toast(host_win, f"✓ {label} sudah dicopy", ok=True)
            return True
        except Exception:
            self._copy_success_toast(host_win, "Gagal menyalin teks", ok=False)
            return False

    def open_file(self, path: str) -> None:
        try:
            if os.name == "nt":
                os.startfile(path)  # type: ignore[attr-defined]
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            try:
                self.messagebox.showerror(APP_TITLE, f"Gagal membuka file:\n{e}")
            except Exception:
                pass

    def open_folder(self, path: str) -> None:
        try:
            p = Path(path)
            if os.name == "nt":
                if p.exists() and p.is_dir():
                    subprocess.Popen(["explorer.exe", str(p)])
                elif p.exists():
                    subprocess.Popen(["explorer.exe", "/select,", str(p)])
                else:
                    subprocess.Popen(["explorer.exe", str(p.parent if p.suffix else p)])
            else:
                subprocess.Popen(["xdg-open", str(p if p.is_dir() else p.parent)])
        except Exception as e:
            self.messagebox.showerror(APP_TITLE, f"Gagal membuka folder:\n{e}")

    def _image_preview_png(self, p: Path) -> Optional[Path]:
        """Convert an image to a temporary PNG for Tk preview without opening another app."""
        try:
            from PIL import Image  # optional acceleration, not required by BASKA SEND
            out = Path(tempfile.gettempdir()) / f"baska_hub_preview_{hashlib.sha1(str(p).encode()).hexdigest()[:12]}.png"
            with Image.open(str(p)) as im:
                im.thumbnail((1100, 800))
                if im.mode not in {"RGB", "RGBA"}:
                    im = im.convert("RGBA")
                im.save(str(out), "PNG")
            return out
        except Exception:
            pass
        if os.name != "nt":
            return None
        try:
            out = Path(tempfile.gettempdir()) / f"baska_hub_preview_{hashlib.sha1(str(p).encode()).hexdigest()[:12]}.png"
            src_ps = "'" + str(p).replace("'", "''") + "'"
            out_ps = "'" + str(out).replace("'", "''") + "'"
            ps = (
                "$ErrorActionPreference='Stop'\n"
                "Add-Type -AssemblyName PresentationCore\n"
                f"$src={src_ps}\n"
                f"$out={out_ps}\n"
                "$u=New-Object System.Uri($src)\n"
                "$bmp=New-Object System.Windows.Media.Imaging.BitmapImage\n"
                "$bmp.BeginInit()\n"
                "$bmp.CacheOption=[System.Windows.Media.Imaging.BitmapCacheOption]::OnLoad\n"
                "$bmp.UriSource=$u\n"
                "$bmp.EndInit()\n"
                "$enc=New-Object System.Windows.Media.Imaging.PngBitmapEncoder\n"
                "$enc.Frames.Add([System.Windows.Media.Imaging.BitmapFrame]::Create($bmp))\n"
                "$fs=[System.IO.File]::Open($out,[System.IO.FileMode]::Create)\n"
                "try {$enc.Save($fs)} finally {$fs.Close()}\n"
            )
            encoded = base64.b64encode(ps.encode("utf-16le")).decode("ascii")
            r = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded], capture_output=True, timeout=20)
            if r.returncode == 0 and out.exists() and out.stat().st_size > 0:
                return out
        except Exception:
            pass
        return None

    def preview_file(self, path: str, parent=None) -> None:
        p = Path(path)
        ext = p.suffix.lower()
        if ext in {".txt", ".csv"}:
            win = self.tk.Toplevel(self.root)
            win.title(f"Preview - {p.name}")
            win.attributes("-topmost", True)
            self._place_bottom_right(win, 700, 520)
            box = self.scrolledtext(win, wrap="word", font=("Consolas", 10), padx=10, pady=10)
            box.pack(fill="both", expand=True)
            try:
                box.insert("1.0", p.read_text(encoding="utf-8", errors="replace")[:300000])
            except Exception as e:
                box.insert("1.0", f"Preview gagal: {e}")
            box.configure(state="disabled")
            return
        if ext in IMAGE_EXTENSIONS:
            preview_path = p if ext in {".png", ".gif", ".ppm", ".pgm"} else self._image_preview_png(p)
            if preview_path:
                try:
                    img = self.tk.PhotoImage(file=str(preview_path))
                    win = self.tk.Toplevel(self.root)
                    win.title(f"Preview - {p.name}")
                    win.attributes("-topmost", True)
                    maxw, maxh = 900, 680
                    factor = max(1, int(max(img.width() / maxw, img.height() / maxh)))
                    disp = img.subsample(factor, factor) if factor > 1 else img
                    lab = self.tk.Label(win, image=disp, bg="#111722")
                    lab.pack(fill="both", expand=True, padx=8, pady=8)
                    win._img = disp
                    win._preview_path = str(preview_path)
                    self._place_bottom_right(win, min(maxw, disp.width() + 16), min(maxh, disp.height() + 16))
                    return
                except Exception:
                    pass
        # PDF and formats without an internal decoder use the configured Windows viewer.
        self.open_file(str(p))

    def show_file_details(self, row: Dict[str, Any], parent=None) -> None:
        p = Path(row.get("file_path") or "")
        try:
            st = p.stat()
            mime = row.get("mime") or mimetypes.guess_type(p.name)[0] or "application/octet-stream"
            h = hashlib.sha256()
            with p.open("rb") as f:
                for chunk in iter(lambda: f.read(1024 * 1024), b""):
                    h.update(chunk)
            details = (
                f"Nama: {p.name}\n"
                f"Tipe: {mime}\n"
                f"Ukuran: {self._human_bytes(st.st_size)}\n"
                f"Diterima: {format_datetime_id(row.get('created_at'))}\n"
                f"Lokasi: {p}\n"
                f"SHA-256: {h.hexdigest()}"
            )
        except Exception as e:
            details = f"Detail file tidak dapat dibaca:\n{e}"
        win = self.tk.Toplevel(self.root)
        win.title("Detail file")
        win.attributes("-topmost", True)
        win.configure(bg="#101722")
        self._place_bottom_right(win, 620, 330)
        self.tk.Label(win, text="Detail file", fg="#f5f7fb", bg="#101722", font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=16, pady=(14, 8))
        box = self.scrolledtext(win, wrap="word", height=10, bg="#171f2d", fg="#f0f3f8", insertbackground="white", relief="flat", font=("Segoe UI", 10), padx=10, pady=9)
        box.pack(fill="both", expand=True, padx=16, pady=(0, 10))
        box.insert("1.0", details)
        box.configure(state="disabled")
        self.tk.Button(win, text="Buka folder", command=lambda: self.open_folder(str(p)), bg="#1a2435", fg="#e7ecf7", relief="flat", padx=14, pady=7).pack(anchor="e", padx=16, pady=(0, 14))


def make_server(app: AppState) -> ThreadingHTTPServer:
    class BoundHandler(Handler):
        pass
    BoundHandler.app_state = app
    host = str(app.cfg.get("host", "0.0.0.0"))
    port = int(app.cfg.get("port", DEFAULT_PORT))
    server = ThreadingHTTPServer((host, port), BoundHandler)
    server.daemon_threads = True
    return server


def serve_http(app: AppState) -> None:
    try:
        app.httpd = make_server(app)
        host, port = app.httpd.server_address[0], app.httpd.server_address[1]
        log(f"Server aktif di {host}:{port}; LAN URL: http://{local_ip()}:{port}")
        app.httpd.serve_forever(poll_interval=0.5)
    except Exception as e:
        log(f"Server gagal: {e}\n{traceback.format_exc()}")
        app.shutdown_event.set()


def queue_pending(app: AppState) -> None:
    try:
        for row in pending_desktop_messages():
            app.popup_queue.put(int(row["id"]))
    except Exception as e:
        log(f"Gagal memuat pesan pending: {e}")


def run_app() -> None:
    cfg = load_config()
    port = int(cfg.get("port", DEFAULT_PORT))
    if server_running(port):
        log(f"{APP_TITLE} sudah berjalan di port {port}; instance kedua dibatalkan.")
        return
    init_db()
    app = AppState(cfg)
    queue_pending(app)
    t = threading.Thread(target=serve_http, args=(app,), name="http-server", daemon=True)
    t.start()
    if os.name == "nt":
        PopupManager(app).start()
    else:
        log("Target utama aplikasi ini Windows. Berjalan tanpa popup native.")
        try:
            while not app.shutdown_event.wait(1):
                pass
        except KeyboardInterrupt:
            pass
    app.shutdown_event.set()
    if app.httpd:
        try:
            app.httpd.shutdown()
        except Exception:
            pass


def startup_command() -> Tuple[str, str]:
    script = str(Path(__file__).resolve())
    py = Path(sys.executable)
    pyw = py.with_name("pythonw.exe") if os.name == "nt" else py
    exe = str(pyw if pyw.exists() else py)
    return exe, f'"{exe}" "{script}" --run'


def install_startup() -> None:
    if os.name != "nt":
        raise RuntimeError("Auto-start ini khusus Windows.")
    _, cmd = startup_command()
    # Remove the old branded task so only SendToCom starts at logon.
    subprocess.run(["schtasks", "/Delete", "/F", "/TN", LEGACY_TASK_NAME], capture_output=True, text=True)
    try:
        r = subprocess.run(["schtasks", "/Create", "/F", "/SC", "ONLOGON", "/TN", TASK_NAME, "/TR", cmd], capture_output=True, text=True, timeout=20)
        if r.returncode == 0:
            print(f"Auto-start terpasang via Task Scheduler: {TASK_NAME}")
            return
        log(f"Task Scheduler gagal, fallback HKCU Run: {r.stderr or r.stdout}")
    except Exception as e:
        log(f"Task Scheduler error, fallback HKCU Run: {e}")
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE) as k:
        try:
            winreg.DeleteValue(k, LEGACY_APP_NAME)
        except FileNotFoundError:
            pass
        winreg.SetValueEx(k, APP_NAME, 0, winreg.REG_SZ, cmd)
    print("Auto-start terpasang via HKCU Run.")


def remove_startup() -> None:
    if os.name != "nt":
        return
    subprocess.run(["schtasks", "/Delete", "/F", "/TN", TASK_NAME], capture_output=True, text=True)
    subprocess.run(["schtasks", "/Delete", "/F", "/TN", LEGACY_TASK_NAME], capture_output=True, text=True)
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE) as k:
            for value_name in (APP_NAME, LEGACY_APP_NAME):
                try:
                    winreg.DeleteValue(k, value_name)
                except FileNotFoundError:
                    pass
    except Exception:
        pass
    print("Auto-start dihapus jika sebelumnya ada.")


def firewall_add() -> None:
    if os.name != "nt":
        raise RuntimeError("Firewall command khusus Windows.")
    cfg = load_config()
    port = int(cfg.get("port", DEFAULT_PORT))
    subprocess.run(["netsh", "advfirewall", "firewall", "delete", "rule", f"name={LEGACY_FIREWALL_RULE_NAME}"], capture_output=True, text=True)
    cmd = ["netsh", "advfirewall", "firewall", "add", "rule", f"name={FIREWALL_RULE_NAME}", "dir=in", "action=allow", "protocol=TCP", f"localport={port}", "profile=private"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout or "Gagal menambah firewall rule").strip())
    print(f"Firewall rule ditambahkan untuk TCP {port}, profile Private.")


def firewall_remove() -> None:
    if os.name != "nt":
        return
    r = subprocess.run(["netsh", "advfirewall", "firewall", "delete", "rule", f"name={FIREWALL_RULE_NAME}"], capture_output=True, text=True)
    subprocess.run(["netsh", "advfirewall", "firewall", "delete", "rule", f"name={LEGACY_FIREWALL_RULE_NAME}"], capture_output=True, text=True)
    print((r.stdout or r.stderr or "Firewall rule dihapus jika ada.").strip())


def server_running(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", int(port)), timeout=0.6):
            return True
    except Exception:
        return False


def launch_background() -> bool:
    cfg = load_config()
    port = int(cfg.get("port", DEFAULT_PORT))
    if server_running(port):
        return False
    script = str(Path(__file__).resolve())
    if os.name == "nt":
        py = Path(sys.executable)
        pyw = py.with_name("pythonw.exe")
        exe = str(pyw if pyw.exists() else py)
        flags = 0x00000008 | 0x00000200
        subprocess.Popen([exe, script, "--run"], cwd=str(Path(script).parent), creationflags=flags, close_fds=True)
    else:
        subprocess.Popen([sys.executable, script, "--run"], cwd=str(Path(script).parent), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    for _ in range(20):
        time.sleep(0.15)
        if server_running(port):
            return True
    return False


def stop_running_instance() -> int:
    """Stop other SendToCom Python processes that run this exact script."""
    if os.name != "nt":
        raise RuntimeError("--stop/--restart process control khusus Windows.")
    script = str(Path(__file__).resolve())
    # PowerShell/WMI is available on Windows 7+ and lets us inspect python/pythonw command lines.
    target_ps = "'" + script.replace("'", "''") + "'"
    ps = (
        f"$self={os.getpid()}; $target={target_ps}; "
        "Get-WmiObject Win32_Process | Where-Object { "
        "$_.ProcessId -ne $self -and $_.Name -match '^pythonw?\\.exe$' -and $_.CommandLine -and $_.CommandLine.Contains($target) "
        "} | ForEach-Object { try { [void]$_.Terminate() } catch {} }"
    )
    encoded = base64.b64encode(ps.encode("utf-16le")).decode("ascii")
    subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded], capture_output=True, timeout=20)
    cfg = load_config()
    port = int(cfg.get("port", DEFAULT_PORT))
    for _ in range(30):
        if not server_running(port):
            break
        time.sleep(0.1)
    return port


def restart_background() -> None:
    port = stop_running_instance()
    started = launch_background()
    running = started or server_running(port)
    print(f"{APP_TITLE} v{VERSION} restart: {'RUNNING' if running else 'GAGAL'}")
    if running:
        print(f"LAN URL     : http://{local_ip()}:{port}")


def status() -> None:
    cfg = load_config()
    port = int(cfg.get("port", DEFAULT_PORT))
    print(f"{APP_TITLE} v{VERSION}")
    print(f"Status      : {'RUNNING' if server_running(port) else 'STOPPED'}")
    print(f"Nama PC     : {cfg.get('device_name', 'BASKA SEND')}")
    print(f"LAN URL     : http://{local_ip()}:{port}")
    print(f"LAN only    : {bool(cfg.get('lan_only', True))}")
    print(f"Max upload  : {cfg.get('max_upload_mb', 50)} MB")
    print(f"File masuk  : {received_files_dir(cfg)}")
    print(f"Organisasi  : {'AKTIF' if cfg.get('organize_received_files', True) else 'NONAKTIF'}")
    print(f"Config JSON : {CONFIG_PATH}")
    print(f"Data folder : {APP_DIR}")
    if FIRST_PIN_PATH.exists():
        print(f"PIN awal    : lihat {FIRST_PIN_PATH}")


def setup_wizard() -> None:
    load_config()
    print(f"\n{APP_TITLE} v{VERSION} - Setup\n")
    while True:
        p1 = input("Buat PIN 4-12 digit: ").strip()
        p2 = input("Ulangi PIN            : ").strip()
        if p1 != p2:
            print("PIN tidak sama. Coba lagi.\n")
            continue
        try:
            set_pin(p1)
            break
        except ValueError as e:
            print(f"{e}\n")
    try:
        install_startup()
    except Exception as e:
        print(f"Auto-start gagal: {e}")
    if os.name == "nt":
        try:
            firewall_add()
        except Exception:
            print("Firewall belum ditambahkan. Jalankan PowerShell sebagai Administrator lalu:")
            print(f'  "{sys.executable}" "{Path(__file__).resolve()}" --firewall-add')
    started = False
    try:
        started = launch_background()
    except Exception as e:
        print(f"Aplikasi belum dapat dijalankan otomatis: {e}")
    cfg = load_config()
    print("\nSetup selesai.")
    print("Status aplikasi : " + ("RUNNING" if (started or server_running(int(cfg.get("port", DEFAULT_PORT)))) else "belum berjalan"))
    print(f"URL perangkat lain: http://{local_ip()}:{int(cfg.get('port', DEFAULT_PORT))}")


def main() -> None:
    parser = argparse.ArgumentParser(description=APP_TITLE)
    parser.add_argument("--run", action="store_true", help="jalankan server (dipakai auto-start)")
    parser.add_argument("--setup", action="store_true", help="setup awal: PIN + auto-start + firewall")
    parser.add_argument("--set-pin", metavar="PIN", help="ubah PIN (4-12 digit)")
    parser.add_argument("--install-startup", action="store_true", help="pasang auto-start saat user login")
    parser.add_argument("--remove-startup", action="store_true", help="hapus auto-start")
    parser.add_argument("--firewall-add", action="store_true", help="izinkan port di Windows Firewall Private profile")
    parser.add_argument("--firewall-remove", action="store_true", help="hapus firewall rule")
    parser.add_argument("--status", action="store_true", help="lihat status dan URL")
    parser.add_argument("--restart", action="store_true", help="hentikan proses lama lalu jalankan versi script ini")
    parser.add_argument("--stop", action="store_true", help="hentikan proses SendToCom yang sedang berjalan")
    args = parser.parse_args()

    if args.setup:
        setup_wizard(); return
    if args.set_pin:
        set_pin(args.set_pin); return
    if args.install_startup:
        load_config(); install_startup(); status(); return
    if args.remove_startup:
        remove_startup(); return
    if args.firewall_add:
        firewall_add(); return
    if args.firewall_remove:
        firewall_remove(); return
    if args.restart:
        restart_background(); return
    if args.stop:
        stop_running_instance(); print(f"{APP_TITLE}: STOPPED"); return
    if args.status:
        status(); return
    run_app()


if __name__ == "__main__":
    main()
