import logging

import requests
from bs4 import BeautifulSoup, NavigableString, Tag

from src.models.job_model import JobListing

HN_DOMAIN = "https://hnhiring.com"

def scrap_hn_job_listing(page: str):
    r = requests.get(url=f"{HN_DOMAIN}/{page}")
    if r.status_code != 200:
        logging.error(f"{r.text}")
        raise Exception(f"Error scraping {page}")

    job_listing = []
    soup = BeautifulSoup(r.content, "html.parser")
    jobs = soup.find("ul", class_="jobs")
    for li in jobs.find_all("li"):
        job_listing.append(
            parse_job(li)
        )

    print(job_listing)


def parse_job(job: Tag) -> JobListing:
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

    return JobListing(
        title=title,
        description=description,
    )

if __name__ == "__main__":
    scrap_hn_job_listing("january-2026")