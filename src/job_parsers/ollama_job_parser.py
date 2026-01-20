import json
from inspect import cleandoc

from ollama import Client

from src.models.job_model import ProcessedJobListing, RawJobListing


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

    def parse(self, job: RawJobListing) -> ProcessedJobListing:
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
            }
        )

        normalized_response = (
            chat_response
                .message
                .content
                .replace("\\_", "_")
        )

        chat_response = json.loads(normalized_response)

        return ProcessedJobListing(
            id = job.job_id,
            title = job.title,
            description = chat_response['description'],
            job_url = chat_response['job_url'],
            company_url = chat_response['company_url'],
            technologies = chat_response['technologies'],
            location = chat_response['job_location'],
            industry = chat_response['industry'],
            is_remote = chat_response['is_remote'],
            salary = chat_response['salary'],
        )
