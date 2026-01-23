import json
import logging
from inspect import cleandoc
from typing import Any

from ollama import Client, ChatResponse

from src.models.job_model import ProcessedJobs, RawJob


class OllamaJobParser:
    def __init__(self):
        self.client = Client(
            host="localhost:11434",
        )
        self._validate_init()

    def _validate_init(self):
        try:
            self.client.list()
        except ConnectionError:
            raise ConnectionError(f"Ollama server not running")
        except Exception as e:
            raise e

        if len(self.client.list().models) == 0:
            raise RuntimeError(f"No Ollama models found")

    @staticmethod
    def _parse_json(chat_response: ChatResponse) -> dict[str, Any]:
        normalized_response = chat_response.message.content.replace("\\_", "_")
        if normalized_response.startswith("```json"):
            normalized_response = normalized_response.replace("```json", "")
            normalized_response = normalized_response.replace("```", "")

        response = json.loads(normalized_response)

        if type(response["is_remote"]) != bool:
            if type(response["is_remote"]) == str and response["is_remote"].lower() == "hybrid":
                response["is_remote"] = True
            else:
                logging.info(f"\"is_remote\" is not boolean, falling back to \"False\": {response["is_remote"]}")
                response["is_remote"] = False

        return response

    def parse(self, job: RawJob) -> ProcessedJobs | None:
        system_prompt = cleandoc("""
            You are an information extraction system.
            You extract structured data and return ONLY valid JSON.
        """)

        user_prompt = cleandoc(f"""
            Extract structured data from the job description below.

            Rules:
            - Return ONLY valid JSON.
            - Do NOT add any explanations or comments.
            - If a field is not explicitly mentioned, set its value to null.
            - Do NOT guess or infer missing information.
            - Keep descriptions concise (max 4 sentences).
            - Technologies must be returned as an array of strings.
            - Industry can be understood business sector.
            - If a role is remote, but any location information is given note this. 
            - You will need to infer industry.
            - Look for benefits/perks 

            JSON schema:
            {{
              "title": string,
              "description": string,
              "job_url": string | null,
              "company_url": string | null,
              "industry": string | null,
              "salary": string | null,
              "job_location": string | null,
              "is_remote": boolean | null,
              "technologies": string[] | null,
              "benefits": string[] | null,"
            }}

            Job title:
            {job.title}

            Job description:
            {" ".join(job.description.splitlines())}
        """)

        chat_response = self.client.chat(
            model="mistral:7b-instruct-q4_0",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            options={
                "temperature": 0.0,
            },
        )

        try:
            chat_response = self._parse_json(chat_response)

            return ProcessedJobs(
                job_id=job.job_id,
                title=job.title,
                posted_date=job.posted_date,
                description=chat_response["description"],
                job_url=chat_response["job_url"],
                company_url=chat_response["company_url"],
                technologies=chat_response["technologies"],
                location=chat_response["job_location"],
                industry=chat_response["industry"],
                is_remote=chat_response["is_remote"],
                salary=chat_response["salary"],
            )
        except Exception as e:
            logging.info(f"Chat response: {chat_response}")
            logging.info(f"Could not parse job {job.job_id}: {e}")
            return None
