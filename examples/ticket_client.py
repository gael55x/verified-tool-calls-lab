"""Example client for vtc.check: create one ticket, retrying with a stable key.

Contract for `python -m vtc.check --client module:function`:

    function(base_url: str, operation_id: str) -> bool

Send the operation id as the Idempotency-Key header on every attempt, return True
only when the service confirmed the ticket, and return False (do not raise) when
you give up. Keep every attempt bounded by a timeout.
"""

import http.client
import json
import time
import urllib.error
import urllib.request


def create_ticket(base_url, operation_id, *, title="printer on fire", timeout=2.0, attempts=3):
    body = json.dumps({"title": title}).encode()
    for attempt in range(1, attempts + 1):
        request = urllib.request.Request(
            base_url.rstrip("/") + "/tickets",
            data=body,
            method="POST",
            headers={"Content-Type": "application/json", "Idempotency-Key": operation_id},
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return 200 <= response.status < 300
        except urllib.error.HTTPError as exc:
            exc.close()
            if exc.code < 500:
                return False  # the service answered and refused; retrying will not help
        except (OSError, http.client.HTTPException):
            pass  # no answer: the write may have happened, so retry with the same key
        if attempt < attempts:
            time.sleep(0.05 * attempt)
    return False
