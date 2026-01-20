import logging
from datetime import datetime, UTC
import dateparser

import requests
from bs4 import BeautifulSoup, NavigableString, Tag
from sqlmodel import Session

from src.db.crud import insert_raw_job_listing
from src.db.engine import get_db, init_db
from src.job_parsers.ollama_job_parser import OllamaJobParser
from src.models.job_model import RawJobListing

HN_DOMAIN = "https://hnhiring.com"

parser = OllamaJobParser()

init_db()

def scrap_hn_job_listing(
    page: str,
    session: Session = get_db().__next__(),
):
    r = requests.get(url=f"{HN_DOMAIN}/{page}")
    if r.status_code != 200:
        logging.error(f"{r.text}")
        raise Exception(f"Error scraping {page}")

    job_listing: list[RawJobListing] = []
    soup = BeautifulSoup(r.content, "html.parser")
    jobs = soup.find("ul", class_="jobs")
    for li in jobs.find_all("li"):
        job_listing.append(
            parse_job(li)
        )

    insert_raw_job_listing(
        session=session,
        job_listing=job_listing,
    )

    # save raw to db
    # parse with LLM
    # save to db



def parse_job(job: Tag) -> RawJobListing:
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

    return RawJobListing(
        title=title,
        description=description,
        posted_date=posted_date,
    )

if __name__ == "__main__":
    scrap_hn_job_listing("january-2026")