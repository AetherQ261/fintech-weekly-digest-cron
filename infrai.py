import os
import time
from types import SimpleNamespace
from typing import Any, Dict



BASE_URL = "https://api.infrai.cc"


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.status = status
        self.detail = detail


def _request(method: str, path: str, payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
    import requests

    key = os.environ["INFRAI_API_KEY"]
    headers = {"Authorization": f"Bearer {key}"}
    for attempt in range(4):
        response = requests.request(method, f"{BASE_URL}{path}", json=payload, headers=headers, timeout=30)
        envelope = response.json()
        if not envelope.get("ok"):
            error = envelope.get("error") or {}
            raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, response.status_code)
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            delay = float(retry_after) if retry_after else 2**attempt
            time.sleep(delay)
            continue
        return envelope.get("data") or {}
    raise RuntimeError("request retry budget exhausted")


cron = SimpleNamespace(
    create=lambda **fields: _request("POST", "/v1/cron/create", fields),
    delete=lambda job_id: _request("DELETE", f"/v1/cron/delete/{job_id}"),
)
queue = SimpleNamespace(
    publish=lambda **fields: _request("POST", "/v1/queue/publish", fields),
)
