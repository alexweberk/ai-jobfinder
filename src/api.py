import os
import time
from collections import deque

from firecrawl import FirecrawlApp  # type: ignore
from openai import OpenAI

from src.logger import logger


def initialize_api_clients() -> tuple[FirecrawlApp, OpenAI]:
    """
    Initialize API clients for Firecrawl and OpenAI using environment variables.
    """
    firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not firecrawl_api_key or not openai_api_key:
        raise ValueError("Missing required API keys in environment variables")

    return FirecrawlApp(api_key=firecrawl_api_key), OpenAI(api_key=openai_api_key)


def wait_for_rate_limit(request_timestamps: deque[float], rate_limit: int, window_size: int) -> None:
    """
    Ensure the rate limit is not exceeded by waiting if necessary.
    """
    current_time = time.time()

    # Remove timestamps older than our window
    while request_timestamps and request_timestamps[0] < current_time - window_size:
        request_timestamps.popleft()

    # If we're at the rate limit, wait until the oldest request expires
    if len(request_timestamps) >= rate_limit:
        sleep_time = request_timestamps[0] - (current_time - window_size) + 0.1  # Add 0.1s buffer
        if sleep_time > 0:
            logger.info(f"Rate limit reached. Waiting {sleep_time:.1f} seconds...")
            time.sleep(sleep_time)
