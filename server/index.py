from db import client as db  # PocketBase client instance
from fastapi import (
    FastAPI,
    status,
    Response,
    Form,
    UploadFile,
    BackgroundTasks,
    HTTPException,
    File,
    Body,
)
from fastapi.middleware.cors import CORSMiddleware
from utils import (
    create_vector_store,
    create_assistant,
    validate_website,
    scrap_website,
    process_stream_event,
    scraping_status,
    session_manager,
    upload_pdf_to_vector_store,
)
from openai import Client
from dotenv import load_dotenv
from pocketbase.client import ClientResponseError, FileUpload
from typing import Optional
from datetime import datetime, timedelta
import uvicorn
import asyncio
from queue import Queue


load_dotenv()
app = FastAPI()
ai = Client()
total_scraped_companies = 0

origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


origins = ["http://localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def run_scraping_task(company_name: str, websites: list[str]):
    """
    Runs the scraping task for the given company URLs.

    This function updates the scraping status for the company, performs the website scraping,
    and handles any exceptions that may occur during the process.

    Args:
        company_name (str): The name of the company for tracking status.
        websites (list[str]): The List of URLs that needs to scraped.

    Returns:
        None
    """
    global total_scraped_companies
    for url in websites:
        try:
            scraping_status[f"{company_name}_{url}"] = {
                "status": "In Progress",
                "start_time": datetime.now(),
                "elapsed": 0,
            }

            end_time = datetime.now() + timedelta(minutes=2)

            while datetime.now() < end_time:
                scrap_website(url, company_name)
                scraping_status[f"{company_name}_{url}"]["elapsed"] = (
                    datetime.now()
                    - scraping_status[f"{company_name}_{url}"]["start_time"]
                ).total_seconds()
                await asyncio.sleep(1)

            scraping_status[f"{company_name}_{url}"]["status"] = "Completed"
            total_scraped_companies += 1

        except Exception as e:
            scraping_status[f"{company_name}_{url}"]["status"] = f"Failed: {str(e)}"
            scraping_status[f"{company_name}_{url}"]["elapsed"] = (
                datetime.now() - scraping_status[f"{company_name}_{url}"]["start_time"]
            ).total_seconds()


@app.post("/scrap")
async def scrap(
    response: Response,
    background_tasks: BackgroundTasks,
    company_name: str = Form(...),
    company_url: str = Form(...),
    persona: str = Form(...),
    customer_name: str = Form(...),
    logo: UploadFile = File(None),
    additional_websites: Optional[str] = Form(None),
    attachments: UploadFile = File(None),
):
    company_name = company_name.lower().strip().replace(" ", "_")
    if not validate_website(company_url):
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"msg": "Provided URL is not valid"}

    if logo:
        logo_binary = await logo.read()
        logo = FileUpload(logo.filename, logo_binary)
    else:
        logo = None

    try:
        db.collection("companies").get_first_list_item(f"company_name='{company_name}'")
        response.status_code = status.HTTP_409_CONFLICT
        return {"message": "This company has already been scraped"}
    except:
        pass

    # TODO : Use actual client and vector store id
    # vector_store_id = create_vector_store(client=ai, company_name=company_name)
    # assistant_id = create_assistant(client=ai, vector_store_id=vector_store_id, company_name=company_name)

    vector_store_id = "vs-1234567890"
    assistant_id = "ad-1234567890"

    try:
        db.collection("companies").create(
            {
                "company_name": company_name,
                "company_url": company_url,
                "vector_store_id": vector_store_id,
                "assistant_id": assistant_id,
                "persona": persona,
                "customer_name": customer_name,
                "logo": logo,
                "additional_websites": additional_websites,
            }
        )

        websites_to_scrape = [company_url]
        print(websites_to_scrape)
        if additional_websites:
            websites_to_scrape.extend(additional_websites.split(","))
        print(websites_to_scrape)

        for url in websites_to_scrape:
            scraping_status[f"{company_name}_{url}"] = {
                "status": "Pending",
                "elapsed": 0,
            }

        background_tasks.add_task(run_scraping_task, company_name, websites_to_scrape)

        response.status_code = status.HTTP_201_CREATED
        return {
            "message": "Company saved and scraping started",
            "company_name": company_name,
        }

    except ClientResponseError as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": f"Failed to save company {e}"}
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"error": f"An unexpected error occurred: {str(e)}"}


@app.get("/scraping_status/{company_name}")
async def get_scraping_status(company_name: str):
    status = scraping_status.get(company_name)
    if status is None:
        return {"status": "Not Found", "company_name": company_name}

    response_data = {"total_scraped": total_scraped_companies, "companies": {}}

    overall_elapsed = 0
    for company_url, status_data in status.items():
        if status_data["status"] == "In Progress":
            status_data["elapsed"] = (
                datetime.now() - status_data["start_time"]
            ).total_seconds()

        response_data["companies"][company_url] = {
            "status": status_data["status"],
            "elapsed": status_data["elapsed"],
        }

        overall_elapsed += status_data["elapsed"]

    response_data["overall_elapsed"] = overall_elapsed

    return response_data


@app.post("/ask")
async def ask_query(
    company_name: str = Body(...), persona: str = Body(...), prompt: str = Body(...)
):
    company_name = company_name.strip().lower().replace(" ", "_")
    key = f"{company_name}<SEP>{persona}"
    if key in session_manager:
        value = session_manager[key]
        assistant_id = value["assistant_id"]
        thread_id = value["thread_id"]
        vector_store_id = value["vector_store_id"]

    else:
        try:
            company = db.collection("companies").get_first_list_item(
                f"company_name='{company_name}'"
            )
            assistant_id = company.assistant_id
            vector_store_id = company.vector_store_id
            thread_id = "fresh_thread_id"
            session_manager[key] = {
                "assistant_id": assistant_id,
                "vector_store_id": vector_store_id,
                "thread_id": thread_id,
            }
        except Exception as e:
            return {"message": "Requested company not found!", "error": e}

    try:
        sentence_queue = Queue()
        buffer_dict = {"buffer": ""}

        ai.beta.threads.messages.create(
            thread_id=thread_id, role="user", content=prompt
        )

        assistant_reply_parts = []

        run = ai.beta.threads.runs.create(
            thread_id=thread_id, assistant_id=assistant_id, stream=True
        )

        for event in run:
            process_stream_event(
                event, assistant_reply_parts, sentence_queue, buffer_dict
            )

        assistant_reply = "".join(assistant_reply_parts)
        return {"answer": assistant_reply}

    except Exception as e:
        return {"message": "Something went wrong while generating response", "error": e}


if __name__ == "__main__":
    uvicorn.run("index:app", port=8000, log_level="info")
