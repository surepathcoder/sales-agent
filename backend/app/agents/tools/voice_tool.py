"""Voice note generator — Mock TTS tool for Swahili and English voice note outreach."""

import logging
import os
import uuid
from typing import Any

logger = logging.getLogger(__name__)


async def generate_voice_note(
  script: str,
  tenant_id: str = "system",
) -> dict[str, Any]:
  """
  MVP: writes a dummy audio file representing the generated voice script and returns its file path and mock URL.
  Production: integrate a Swahili-optimized text-to-speech API (e.g., ElevenLabs or local TTS service).
  """
  # Determine uploads path relative to backend directory
  base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
  upload_dir = os.path.join(base_dir, "uploads", "voice_notes")
  
  # Ensure target directory exists
  os.makedirs(upload_dir, exist_ok=True)
  
  filename = f"voice_note_{uuid.uuid4().hex[:12]}.mp3"
  filepath = os.path.join(upload_dir, filename)
  
  # Write dummy MP3 header bytes
  # ID3v2.3 minimal header + mock frame
  dummy_mp3_data = b"ID3\x03\x00\x00\x00\x00\x00\x23TSSE\x00\x00\x00\x0f\x00\x00\x03Lavf60.3.100\x00\x00\x00\x00" + b"\xff\xfb\x90\x44" * 100
  
  try:
    with open(filepath, "wb") as f:
      f.write(dummy_mp3_data)
  except Exception as e:
    logger.error("Failed to write mock voice note file: %s", e)
    filepath = ""
    filename = ""

  logger.info("Voice Note [%s] script='%s' file=%s", tenant_id, script, filepath)
  
  return {
    "status": "generated",
    "filename": filename,
    "filepath": filepath,
    "url": f"/uploads/voice_notes/{filename}" if filename else "",
    "script_preview": script[:100],
    "duration_seconds": 15.0,
    "mock": True,
  }
