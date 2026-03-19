import sys
import logging
from typing import Dict, Any, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.core.config import settings
from app.core.parser_engine import parse_resume

# Force stdout flush for real-time logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("resume_parser")

app = FastAPI(
    title="Resume Parser",
    version="1.0.0",
    description="Hybrid Rule-based Resume Parser",
)


class ParseRequest(BaseModel):
    resume_object: Optional[Dict[str, str]] = None
    resume_text: str


class ParseResponse(BaseModel):
    success: bool
    data: Dict[str, Any] = {}
    error: Optional[str] = None
    confidence: Dict[str, float] = {}
    overall_confidence: float = 0.0
    sections_detected: list = []


@app.post("/parse-resume", response_model=ParseResponse)
async def parse_resume_endpoint(request: ParseRequest):
    if not request.resume_text or not request.resume_text.strip():
        raise HTTPException(status_code=400, detail="Empty resume text")

    logger.info("Parsing resume (%d chars)", len(request.resume_text))
    result = parse_resume(request.resume_text)

    if not result["success"]:
        logger.error("Parse failed: %s", result.get("error"))
    else:
        logger.info(
            "Parse complete — success=%s, confidence=%s, sections=%s",
            result["success"],
            result.get("overall_confidence", 0),
            result.get("sections_detected", []),
        )

    return result


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=False)
