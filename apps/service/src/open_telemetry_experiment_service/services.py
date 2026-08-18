import random

from fastapi import HTTPException
from loguru import logger

from open_telemetry_experiment_service.config import config
from open_telemetry_experiment_service.schemas import ProcessResponse


class ProcessService:
    async def process(self, text: str) -> ProcessResponse:
        logger.info("Processing text (text={text})", text=text)

        if _should_fail():
            logger.error("Injected failure while processing (text={text})", text=text)
            raise HTTPException(status_code=500, detail="injected failure")

        result = ProcessResponse(result=text.upper(), word_count=len(text.split()))

        logger.info("Processed text (text={text}, word_count={word_count})", text=text, word_count=result.word_count)
        return result


def _should_fail() -> bool:
    return random.random() < config.FAILURE_RATE
