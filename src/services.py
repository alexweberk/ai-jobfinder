import asyncio
import json
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Awaitable, Optional

from firecrawl import FirecrawlApp  # type: ignore
from openai import OpenAI
from tqdm.asyncio import tqdm as atqdm

from src.logger import logger
from src.types import ApplyLinksSchema, JobSchema, JobSchemas, ScrapeEndpointJsonSchema


def scrape_jobs_page(firecrawl: FirecrawlApp, url: str, output_dir: Path) -> Optional[ScrapeEndpointJsonSchema]:
    """
    Scrape job listings from a given URL using the Firecrawl API.
    If the scrape result is already cached, it will be returned from the cache.
    """
    safe_url = url.replace("/", "_")
    scrape_result_path = Path(f"{output_dir}/scrape_result-{safe_url}.json")

    if scrape_result_path.exists():
        with open(scrape_result_path, "r") as f:
            return json.load(f)

    try:
        scrape_result = firecrawl.scrape_url(
            url,
            {
                "formats": ["json"],
                "jsonOptions": {"schema": ApplyLinksSchema.model_json_schema()},
            },
        )
        if not scrape_result or "json" not in scrape_result:
            raise ValueError("Failed to get valid scrape result")
    except Exception:
        logger.exception(f"Failed to scrape jobs from {url}", exc_info=True)
        return None
    else:
        # Save the scrape result to a file
        with open(scrape_result_path, "w") as f:
            json.dump(scrape_result, f, indent=2, ensure_ascii=False)
        return scrape_result


def extract_job_data(link: str, firecrawl: FirecrawlApp) -> Optional[JobSchema]:
    """
    Extract job data from a given link using the Firecrawl API.
    """
    try:
        result = firecrawl.extract(
            [link],
            {
                "prompt": "Extract details about the job posting. Leave fields blank if uncertain. Do not make things up.",
                "schema": JobSchema.model_json_schema(),
            },
        )
        if not result.get("success"):
            logger.warning(f"Failed to extract data from {link}. Response: {result}")
            return None

        data = result.get("data")
        if not data:
            logger.warning(f"No data extracted from {link}")
            return None

        return JobSchema(**data)

    except Exception:
        logger.exception(f"Failed to extract data from {link}", exc_info=True)
        return None


async def extract_job_data_async(
    link: str,
    firecrawl: FirecrawlApp,
    request_timestamps: deque[float],
    rate_limit: int,
    window_size: int,
    semaphore: asyncio.Semaphore,
) -> Optional[JobSchema]:
    """
    Asynchronous version of extract_job_data that handles rate limiting.
    """
    async with semaphore:  # Control concurrent requests
        # Wait for rate limit in an async way
        current_time = time.time()
        while len(request_timestamps) >= rate_limit:
            oldest_time = request_timestamps[0]
            if oldest_time > current_time - window_size:
                wait_time = oldest_time - (current_time - window_size) + 0.1
                await asyncio.sleep(wait_time)
                current_time = time.time()
            else:
                request_timestamps.popleft()

        try:
            # Run the synchronous Firecrawl API call in a thread pool
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as pool:
                result = await loop.run_in_executor(
                    pool,
                    lambda: firecrawl.extract(
                        [link],
                        {
                            "prompt": "Extract details about the job posting. Leave fields blank if uncertain. Do not make things up.",
                            "schema": JobSchema.model_json_schema(),
                        },
                    ),
                )

            if not result.get("success"):
                logger.warning(f"Failed to extract data from {link}. Response: {result}")
                return None

            data = result.get("data")
            if not data:
                logger.warning(f"No data extracted from {link}")
                return None

            request_timestamps.append(time.time())
            logger.info(f"Successfully processed {link}")
            return JobSchema(**data)

        except Exception:
            logger.exception(f"Failed to extract data from {link}", exc_info=True)
            return None


async def process_job_links_async(
    links: list[str],
    firecrawl: FirecrawlApp,
    max_jobs: int = 20,
    rate_limit: int = 10,
    window_size: int = 60,
    max_concurrent: int = 5,
) -> list[JobSchema]:
    """
    Process job links concurrently while respecting rate limits.

    Args:
        links: List of job links to process
        firecrawl: FirecrawlApp instance
        url: The URL of the job listings page
        max_jobs: Maximum number of jobs to process
        rate_limit: Maximum number of requests per window
        window_size: Time window in seconds for rate limiting
        max_concurrent: Maximum number of concurrent requests
    """
    request_timestamps: deque[float] = deque()
    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_links() -> list[JobSchema]:
        tasks: list[Awaitable[Optional[JobSchema]]] = [
            extract_job_data_async(
                link,
                firecrawl,
                request_timestamps,
                rate_limit,
                window_size,
                semaphore,
            )
            for link in links[:max_jobs]
        ]

        results: list[JobSchema] = []
        async for coro in atqdm(
            asyncio.as_completed(tasks),
            total=len(tasks),
            desc="Processing job links",
            unit="job",
        ):
            result = await coro
            if isinstance(result, JobSchema):
                results.append(result)

        return results

    return await process_links()


def process_job_links(
    links: list[str],
    firecrawl: FirecrawlApp,
    url: str,
    max_jobs: int = 20,
    rate_limit: int = 10,
    window_size: int = 60,
    output_dir: Path = Path("results"),
) -> list[JobSchema]:
    """
    Synchronous wrapper for the asynchronous process_job_links_async function.
    """
    safe_url = url.replace("/", "_")
    processed_jobs_path = Path(f"{output_dir}/processed_jobs-{safe_url}.json")
    if processed_jobs_path.exists():
        with open(processed_jobs_path, "r") as f:
            return [JobSchema(**job) for job in json.load(f)]

    return asyncio.run(
        process_job_links_async(
            links,
            firecrawl,
            max_jobs=max_jobs,
            rate_limit=rate_limit,
            window_size=window_size,
        )
    )


def get_job_recommendations(
    openai: OpenAI,
    resume: str,
    url: str,
    jobs: list[JobSchema],
    num_recommendations: int = 5,
    output_dir: Path = Path("results"),
) -> JobSchemas | None:
    """
    Query the OpenAI API to get job recommendations based on a resume and job listings.
    If the recommendations are already cached, they will be returned from the cache.

    Returns a JSON list of the top 5 recommended roles.
    """
    safe_url = url.replace("/", "_")
    recommendations_path = Path(f"{output_dir}/recommendations-{safe_url}.json")

    if recommendations_path.exists():
        with open(recommendations_path, "r") as f:
            try:
                data = json.load(f)
                # Handle both formats: direct list or wrapped in jobs key
                if isinstance(data, list):
                    return JobSchemas(jobs=[JobSchema(**job) for job in data])
                return JobSchemas(**data)
            except json.JSONDecodeError:
                # If the file is empty or invalid, we will rerun the process
                pass

    prompt = f"""
    <instructions>
    Analyze the resume and job listings, and return a JSON list of the top {num_recommendations} roles that best fit the candidate's experience and skills.
    The output should be a valid JSON array of {num_recommendations} objects.
    </instructions>

    <resume>
    {resume}
    </resume>

    <job_listings>
    {json.dumps([job.model_dump() for job in jobs], indent=2)}
    </job_listings>
    """

    try:
        completion = openai.beta.chat.completions.parse(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format=JobSchemas,
        )

        if not completion.choices:
            raise ValueError("No choices returned from OpenAI API")

        response_content = completion.choices[0].message.content.strip()  # type: ignore
        if not response_content:
            raise ValueError("Empty response from OpenAI API")

        result = JobSchemas(**json.loads(response_content))

        # Save with the correct structure
        with open(recommendations_path, "w") as f:
            json.dump(
                {"jobs": [job.model_dump() for job in result.jobs]},
                f,
                indent=2,
                ensure_ascii=False,
            )

        return result

    except json.JSONDecodeError as e:
        logger.exception(f"Failed to parse OpenAI API response: {e}")
        return None
    except Exception as e:
        logger.exception(f"Error getting job recommendations: {e}")
        return None
