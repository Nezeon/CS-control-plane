import json
import logging
import re

from app.config import settings

logger = logging.getLogger("services.claude")


class ClaudeService:
    def __init__(self):
        self.model = settings.CLAUDE_MODEL
        self._client = None

    @property
    def client(self):
        if self._client is None:
            if not settings.ANTHROPIC_API_KEY:
                return None
            import anthropic
            self._client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        return self._client

    def generate_sync(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> dict:
        """
        Call Claude API synchronously. Used by Celery tasks and agents.
        Returns {"content": str, "input_tokens": int, "output_tokens": int, "model": str}
        On error returns {"error": str, "detail": str} — never raises.
        """
        if self.client is None:
            return {
                "error": "api_key_missing",
                "detail": "ANTHROPIC_API_KEY is not set in environment",
            }

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )
            content = response.content[0].text
            return {
                "content": content,
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "model": response.model,
            }
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return {"error": "api_call_failed", "detail": str(e)}

    def parse_json_response(self, content: str) -> dict:
        """
        Extract JSON from Claude's response.
        Handles markdown ```json ... ``` fences.
        On parse failure returns {"error": "parse_failed", "raw": content}.
        """
        # Try to extract JSON from code fences
        fence_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", content, re.DOTALL)
        json_str = fence_match.group(1) if fence_match else content

        try:
            return json.loads(json_str.strip())
        except json.JSONDecodeError:
            # Try the whole content as-is
            try:
                return json.loads(content.strip())
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON from Claude response: {content[:200]}")
                return {"error": "parse_failed", "raw": content[:1000]}
