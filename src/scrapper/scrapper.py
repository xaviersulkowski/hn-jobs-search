import logging
from datetime import datetime, UTC
import dateparser

import requests
import tqdm
from bs4 import BeautifulSoup, NavigableString, Tag
from sqlmodel import Session

from src.db.crud import upsert_jobs, select_not_processed_jobs
from src.db.engine import get_db, init_db
from src.job_parsers.ollama_job_parser import OllamaJobParser
from src.models.job_model import RawJob, ProcessedJobs, HNJobPosting

HN_DOMAIN = "https://hnhiring.com"

llm_parser = OllamaJobParser()

init_db()

def scrap_hn_job_listing(
    page: str,
    session: Session,
):

    r = requests.get(url=f"{HN_DOMAIN}/{page}")
    if r.status_code != 200:
        logging.error(f"{r.text}")
        raise Exception(f"Error scraping {page}")

    jobs_to_add: list[RawJob] = []
    soup = BeautifulSoup(r.content, "html.parser")
    jobs = soup.find("ul", class_="jobs")
    for li in jobs.find_all("li"):
        job = parse_job(li)
        jobs_to_add.append(
            RawJob.of(job)
        )

    if len(jobs_to_add) > 0:
        logging.info(f"Adding {len(jobs_to_add)} new jobs")
        upsert_jobs(
            session=session,
            model=RawJob,
            job_listing=jobs_to_add,
        )
    else:
        logging.info("No new jobs")


def process_raw_job_listing(
    session: Session,
):
    parsed = []

    for cnt, job in tqdm.tqdm(enumerate(select_not_processed_jobs(session=session))):
        try:
            parsed_job = llm_parser.parse(job=job)
            if parsed_job:
                parsed.append(
                    parsed_job
                )
        except Exception as e:
            logging.error(f"Error parsing {job.job_id}: {e}. Continuing...")
            continue

        if cnt % 10 == 0:
            logging.info(f"Processed {cnt} jobs... Saving partial results.")
            upsert_jobs(
                session=session,
                model=ProcessedJobs,
                job_listing=parsed,
            )
            parsed = []


def parse_job(job: Tag) -> HNJobPosting:
    body = job.find("div", class_="body")

    title = ""
    for child in body.children:
        if isinstance(child, NavigableString):
            title = child.strip()
            if title:
                break

    description = "\n\n".join(
        p.get_text(strip=True) for p in body.find_all("p")
    )

    date_span = job.select_one("div.user span.type-info")
    posted_date = None

    if date_span:
        posted_date = dateparser.parse(
            date_span.get_text(strip=True),
            settings={
                "RELATIVE_BASE": datetime.now(UTC),
                "TIMEZONE": "UTC",
                "RETURN_AS_TIMEZONE_AWARE": False,
            }
        )

    return HNJobPosting(
        title=title,
        description=description,
        posted_date=posted_date,
    )

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    session = get_db().__next__()
    scrap_hn_job_listing(
        "january-2026",
        session
    )
    process_raw_job_listing(
        session
    )