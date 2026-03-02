import logging

logger = logging.getLogger("services.fathom_mock")


class FathomService:
    """Mock Fathom integration. Returns realistic fake call data."""

    def get_recent_recordings(self, limit: int = 10) -> list[dict]:
        """Mock: return list of recent call recordings."""
        recordings = [
            {
                "id": f"fathom-rec-{i}",
                "title": f"Customer Call #{i}",
                "date": f"2026-02-{20 + (i % 8):02d}",
                "duration_minutes": 30 + (i * 7) % 60,
                "participants": ["Vignesh", f"Contact_{i}"],
            }
            for i in range(1, min(limit + 1, 11))
        ]
        return recordings

    def get_recording_transcript(self, recording_id: str) -> dict:
        """Mock: return a fake transcript."""
        return {
            "recording_id": recording_id,
            "transcript": (
                "This is a mock transcript. Customer discussed deployment timeline concerns "
                "and asked about the upcoming product update. Team reviewed scan configuration "
                "options and agreed on a follow-up session next week. Some concerns were raised "
                "about integration compatibility with the new firewall rules."
            ),
            "duration_minutes": 45,
            "participants": ["Vignesh", "John Doe (Acme Corp)"],
            "date": "2026-02-25",
        }
