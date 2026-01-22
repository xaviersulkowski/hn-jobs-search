import os

from typing import Generator
from sqlmodel import create_engine, SQLModel, Session

from src.models.job_model import RawJob, ProcessedJobs

db_path = os.path.join(os.path.dirname(__file__), "..", "..", "db")

if not os.path.exists(db_path):
    os.makedirs(db_path)

engine = create_engine(f"sqlite:///{os.path.join(db_path, "hn-jobs-search.db")}")


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


def init_db():
    SQLModel.metadata.create_all(engine)
