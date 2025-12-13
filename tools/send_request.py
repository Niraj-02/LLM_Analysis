from langchain_core.tools import tool
import requests
import json
from typing import Any, Dict, Optional

@tool
def post_request(url: str, payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Any:
    """
    Send an HTTP POST request to the given URL with the provided payload.
    This function handles quiz submissions. 
    It returns the server response, but ensures:
    - we NEVER delete the URL
    - if delay >= 180 seconds, we STOP retrying and move on
    - the agent always receives the URL needed to continue
    """

    headers = headers or {"Content-Type": "application/json"}
    try:
        print(f"\nSending Answer \n{json.dumps(payload, indent=4)}\n to url: {url}")
        response = requests.post(url, json=payload, headers=headers)

        # Raise on 4xx/5xx
        response.raise_for_status()

        # Parse JSON if possible
        data = response.json()

        delay = data.get("delay", 0)
        delay = delay if isinstance(delay, (int, float)) else 0

        correct = data.get("correct")
        reason = data.get("reason")
        next_url = data.get("url")

        # -----------------------------
        # NEW LOGIC: STOP AFTER 180 SEC
        # -----------------------------
        # If total time exceeds 180 seconds, 
        # return the URL as-is and move on.
        if delay >= 180:
            cleaned = {
                "correct": correct,
                "reason": reason,
                "url": next_url,   # could be None → agent ends
                "delay": delay
            }
            print("Got the response: \n", json.dumps(cleaned, indent=4), '\n')
            return cleaned

        # -----------------------------
        # NORMAL CASE (<180 sec)
        # -----------------------------
        # Always keep the URL so agent can retry or continue.
        cleaned = {
            "correct": correct,
            "reason": reason,
            "url": next_url,
            "delay": delay
        }

        print("Got the response: \n", json.dumps(cleaned, indent=4), '\n')
        return cleaned


    except requests.HTTPError as e:
        err_resp = e.response
        try:
            err_data = err_resp.json()
        except ValueError:
            err_data = err_resp.text

        print("HTTP Error Response:\n", err_data)
        return err_data

    except Exception as e:
        print("Unexpected error:", e)
        return str(e)
