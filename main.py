import json
from pathlib import Path

import typer
from dotenv import load_dotenv

from src.api import initialize_api_clients
from src.logger import logger
from src.services import get_job_recommendations, process_job_links, scrape_jobs_page

# Load environment variables
load_dotenv(override=True)

# Create Typer app
app = typer.Typer(
    name="ai-jobfinder",
    help="AI-powered job finder that matches your resume with job listings",
)


@app.command()
def main(
    jobs_url: str = typer.Option(
        "https://www.anthropic.com/jobs",
        "--jobs-url",
        "-u",
        help="URL of the jobs page to scrape",
    ),
    resume_path: Path = typer.Option(
        "resume.txt",
        "--resume-path",
        "-r",
        help="Path to your resume file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    max_jobs: int = typer.Option(
        10,
        "--max-jobs",
        "-m",
        help="Maximum number of jobs to scrape",
        min=1,
        max=10000,
    ),
    num_recommendations: int = typer.Option(
        5,
        "--num-recommendations",
        "-n",
        help="Number of job recommendations to return",
        min=1,
        max=20,
    ),
    rate_limit: int = typer.Option(
        10,
        "--rate-limit",
        "-l",
        help="Rate limit for API requests per minute",
        min=1,
        max=60,
    ),
    window_size: int = typer.Option(
        60,
        "--window-size",
        "-w",
        help="Time window in seconds for rate limiting",
        min=1,
        max=3600,
    ),
    output_dir: Path = typer.Option(
        "results",
        "--output-dir",
        "-o",
        help="Directory to save the results",
    ),
) -> None:
    """
    Main function orchestrating the job scraping, extraction, and recommendation processes.
    """
    try:
        # Initialize API clients
        firecrawl, openai = initialize_api_clients()

        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Load resume with explicit encoding
        with open(resume_path, "r", encoding="utf-8") as f:
            resume = f.read()
        if not resume:
            raise ValueError(f"Failed to load resume from {resume_path}")
        logger.info(f"Loaded resume from {resume_path}")

        # Scrape jobs page
        scrape_result = scrape_jobs_page(firecrawl, jobs_url, output_dir)
        if not scrape_result:
            raise ValueError("Failed to scrape jobs from the jobs page")

        apply_links = scrape_result["json"].get("apply_links", [])
        if not apply_links:
            raise ValueError("No apply links found on the jobs page")

        logger.info(f"Successfully scraped {len(apply_links)} apply links")

        # Extract job data
        jobs = process_job_links(
            apply_links,
            firecrawl,
            jobs_url,
            max_jobs=max_jobs,
            rate_limit=rate_limit,
            window_size=window_size,
        )
        if not jobs:
            raise ValueError("No job data extracted")

        logger.info(f"Successfully extracted data from {len(jobs)} jobs")

        # Get recommendations
        recommended_jobs = get_job_recommendations(
            openai,
            resume,
            jobs_url,
            jobs,
            num_recommendations=num_recommendations,
            output_dir=output_dir,
        )
        if not recommended_jobs:
            raise ValueError("No job recommendations received")

        logger.info(f"Received {len(recommended_jobs.jobs)} job recommendations")

        # Output results
        logger.info("\nRecommended jobs:")
        for job in recommended_jobs.jobs:
            logger.info(json.dumps(job.model_dump(), indent=2))

    except Exception:
        logger.exception("Main execution failed")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
