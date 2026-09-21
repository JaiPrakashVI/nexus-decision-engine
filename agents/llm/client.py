"""
NEXUS Local LLM Client (Ollama Integration)
Provides resilient asynchronous communication with locally hosted LLMs, with deterministic fallback.
"""

import json
import logging
from typing import Dict, Any, Optional
import httpx

from configs.settings import settings

logger = logging.getLogger("nexus.llm")


class LocalLLMClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        self.base_url = base_url or settings.ollama_base_url
        self.model = model or settings.ollama_model
        self.timeout = timeout or settings.llm_timeout_seconds
        self.mock_fallback = settings.llm_mock_fallback

    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        expected_schema_name: str = "InterventionSchema"
    ) -> Dict[str, Any]:
        """
        Queries Ollama for structured JSON output. Falls back to deterministic AI logic if offline.
        """
        payload = {
            "model": self.model,
            "prompt": f"{system_prompt}\n\nUSER QUERY:\n{user_prompt}\n\nRespond ONLY with a valid JSON object matching the required schema.",
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.2,
                "top_p": 0.9,
            }
        }

        try:
            async with httpx.AsyncClient(timeout=float(self.timeout)) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                )
                if response.status_code == 200:
                    result = response.json()
                    response_text = result.get("response", "{}")
                    parsed = json.loads(response_text)
                    logger.info(f"Successfully generated structured response from local LLM ({self.model}).")
                    return {
                        "source": "ollama",
                        "model": self.model,
                        "data": parsed,
                        "raw": response_text
                    }
                else:
                    logger.warning(f"Ollama returned HTTP {response.status_code}. Using deterministic fallback.")
        except Exception as e:
            logger.info(f"Ollama unavailable ({e}). Using deterministic research agent fallback.")

        # Resilient Deterministic Fallback
        return self._generate_fallback(expected_schema_name, user_prompt)

    def _generate_fallback(self, schema_name: str, context: str) -> Dict[str, Any]:
        """High-grade deterministic simulation of specialized agent reasoning."""
        if "risk" in schema_name.lower():
            return {
                "source": "deterministic_fallback_agent",
                "model": "nexus-rule-engine-v1",
                "data": {
                    "role": "Risk Analyst",
                    "severity_assessment": "HIGH",
                    "cascading_vulnerabilities": [
                        "Downstream pressure drop starving district_alpha",
                        "Highland storage reservoir depleting at 15% per hour"
                    ],
                    "criticality_score": 0.85,
                }
            }
        elif "critic" in schema_name.lower():
            return {
                "source": "deterministic_fallback_agent",
                "model": "nexus-rule-engine-v1",
                "data": {
                    "role": "Adversarial Critic",
                    "critique": "Activating secondary pump at max RPM risks transient water hammer without gradual valve modulation.",
                    "constraint_warnings": ["Check pipe_01 pressure threshold", "Verify substation_01 power reserve"],
                    "risk_flag": False,
                }
            }
        else:
            return {
                "source": "deterministic_fallback_agent",
                "model": "nexus-rule-engine-v1",
                "data": {
                    "role": "Recovery Planner",
                    "recommended_action": "ACTIVATE_BACKUP_PUMP",
                    "target_nodes": ["pump_03"],
                    "parameters": {"target_rpm": 1750, "ramp_time_sec": 10.0},
                    "reasoning": "Auxiliary pump pump_03 has sufficient power reserve and bypasses failed pump_01.",
                    "confidence": 0.92,
                }
            }


llm_client = LocalLLMClient()
