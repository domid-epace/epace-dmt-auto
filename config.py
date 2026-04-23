import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env", override=True)

ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
MODEL: str = "claude-sonnet-4-6"

LEADS_FILE: Path = Path(__file__).parent / "leads.csv"
