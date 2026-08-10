"""CP1 — Structured logging.

`print("client abc hỏi gì đó")` là log cho người đọc. Cloud (Railway, Render,
Cloud Run, Datadog...) đọc log bằng máy: một dòng = một JSON object thì mới
lọc/đếm/cảnh báo được. Đây là khác biệt lớn giữa localhost và production.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone


def utc_now_iso() -> str:
    """CHO SẴN — thời điểm hiện tại theo ISO-8601, múi giờ UTC."""
    return datetime.now(timezone.utc).isoformat()


def emit(event: str, severity: str = "INFO", **fields) -> str:
    """Ghi một dòng log JSON ra stdout."""
    log_dict = {
        "event": event,
        "severity": severity.upper(),
        "ts": utc_now_iso(),
    }
    log_dict.update(fields)
    log_str = json.dumps(log_dict, ensure_ascii=False)
    print(log_str)
    return log_str

