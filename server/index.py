from db import client as db  # PocketBase client instance
from fastapi import (
    FastAPI,
    status,
    Response,
    Form,
    UploadFile,
    BackgroundTasks,
    HTTPException,
    Body,
)
from fastapi.middleware.cors import CORSMiddleware
from utils import (
    create_vector_store,
    create_assistant,
    validate_website,
    scrap_website,
    process_stream_event,
)
from openai import Client
from dotenv import load_dotenv
from pocketbase.client import ClientResponseError, FileUpload
from typing import Optional
import uvicorn
from queue import Queue

load_dotenv()
app = FastAPI()
ai = Client()

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

scraping_status = dict()
session_manager = dict()


async def run_scraping_task(company_url: str, company_name: str):
    """Runs the scraping task for the specified company URL.

    This function updates the scraping status for the company, performs the website scraping,
    and handles any exceptions that may occur during the process.

    Args:
        company_url (str): The URL of the company's website to scrape.
        company_name (str): The name of the company for tracking status.

    Returns:
        None
    """
    try:
        # Update the status to "In Progress"
        scraping_status[company_name] = "In Progress"
        scrap_website(company_url, company_name)
        scraping_status[company_name] = "Completed"
    except Exception as e:
        scraping_status[company_name] = f"Failed: {str(e)}"


@app.post("/scrap")
async def scrap(
    response: Response,
    background_tasks: BackgroundTasks,
    company_name: str = Form(...),
    company_url: str = Form(...),
    persona: str = Form(...),
    customer_name: str = Form(...),
    logo: Optional[UploadFile] = Form(None),
    additional_websites: Optional[str] = Form(None),
    attachments: Optional[UploadFile] = Form(None),
):
    """Handles the scraping of a company's website and stores its details.

    Validates the provided URL, checks if the company has already been scraped,
    and saves the company's information in the database. Initiates the scraping task
    in the background if the company is new.

    Args:
        response (Response): The response object to modify the response status.
        background_tasks (BackgroundTasks): The background tasks to schedule scraping.
        company_name (str): The name of the company to be scraped.
        company_url (str): The URL of the company's website to scrape.
        persona (str): The persona to associate with the company.
        customer_name (str): The name of the customer associated with the company.
        logo (Optional[UploadFile], optional): The logo file for the company. Defaults to Form(None).
        additional_websites (Optional[str], optional): Any additional websites associated with the company. Defaults to Form(None).
        attachments (Optional[UploadFile], optional): Any attachments related to the company. Defaults to Form(None).

    Returns:
        dict: A message indicating the result of the operation, including any error details if applicable.
    """
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
        return {"message": "This company has already been scrapped"}
    except:
        pass

    # TODO : Use actual client and vector store id
    vector_store_id = "vector_store_1234"
    assistant_id = "assistant_id_1234"

    try:
        db.collection("companies").create(
            {
                "company_name": company_name.lower(),
                "company_url": company_url,
                "vector_store_id": vector_store_id,
                "assistant_id": assistant_id,
                "persona": persona,
                "customer_name": customer_name,
                "logo": logo,
                "additional_websites": additional_websites,
            }
        )

        scraping_status[company_name] = "Pending"

        background_tasks.add_task(run_scraping_task, company_url, company_name)

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
    """Retrieves the scraping status of the specified company.

    This endpoint checks the current scraping status for the given company name
    and returns the status if found; otherwise, it indicates that the company
    was not found in the status records.

    Args:
        company_name (str): The name of the company to check the scraping status for.

    Returns:
        dict: A dictionary containing the scraping status and the company name,
              or a message indicating that the company was not found.
    """

    status = scraping_status.get(company_name)  # Check the status dictionary
    if status is None:
        return {"status": "Not Found", "company_name": company_name}

    return {"status": status, "company_name": company_name}


@app.get("/companies/{company_name}")
async def get_company(company_name: str):
    try:
        companies = db.collection("companies").get_full_list()
        company = next((c for c in companies if c.company_name == company_name), None)
        if company:
            return company
        else:
            raise HTTPException(status_code=404, detail="Company not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/companies")
async def get_all_companies():
    try:
        companies = db.collection("companies").get_full_list()
        return [company for company in companies]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
            # thread_id = ai.beta.threads.create().id
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
