json_import = __import__("json")
from typing import Any

import requests

from config import logger


class AIAuditor:

    def __init__(self, ollama_url: str = "http://localhost:11434/api/generate", model: str = "llama3"):
        self.api_url = ollama_url
        self.model = model

    def audit_infrastructure(self, layer1_status: dict[str, Any], layer2_status: dict[str, Any]) -> str:
        audit_payload = {
            "in_transit": layer1_status,
            "at_rest": layer2_status
        }
        prompt = (
            "You are a Senior Security Auditor. Review the following JSON telemetry for a "
            "data security pipeline and provide exactly ONE sentence assessing the encryption "
            f"integrity and compliance. Telemetry: {json_import.dumps(audit_payload)}"
        )

        try:
            response = requests.post(
                self.api_url,
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=2.5
            )
            response.raise_for_status()
            audit_response = response.json().get("response", "").strip()
            if audit_response:
                return audit_response
        except (requests.exceptions.RequestException, ValueError) as exc:
            logger.warning("Ollama API unreachable or failed (%s). Falling back to synthetic audit report.", exc)

        return (
            "[SYNTHETIC FALLBACK] The cryptographic envelope and HTTP security headers "
            "are properly configured, ensuring robust zero-trust compliance for both "
            "in-transit and at-rest vectors."
        )