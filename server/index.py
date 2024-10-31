from db import client as db  # PocketBase client instance
from fastapi import FastAPI, status, Response, Form, UploadFile, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from utils import create_vector_store, create_assistant, validate_website, scrap_website
from openai import Client
from dotenv import load_dotenv
from pocketbase.client import ClientResponseError, FileUpload
from typing import Optional
import uvicorn

load_dotenv()
app = FastAPI()
ai = Client()

scraping_status = dict()

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


async def run_scraping_task(company_url: str, company_name: str):
    """_summary_

    Args:
        company_url (str): _description_
        company_name (str): _description_
    """
    try:
        # Update the status to "In Progress"
        scraping_status[company_name] = "In Progress"

        # Perform the website scraping (could take time)
        scrap_website(company_url, company_name)

        # Mark status as "Completed" once done
        scraping_status[company_name] = "Completed"
    except Exception as e:
        # If an error occurs, mark status as "Failed"
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
    """_summary_

    Args:
        response (Response): _description_
        background_tasks (BackgroundTasks): _description_
        company_name (str, optional): _description_. Defaults to Form(...).
        company_url (str, optional): _description_. Defaults to Form(...).
        persona (str, optional): _description_. Defaults to Form(...).
        customer_name (str, optional): _description_. Defaults to Form(...).
        logo (Optional[UploadFile], optional): _description_. Defaults to Form(None).
        additional_websites (Optional[str], optional): _description_. Defaults to Form(None).
        attachments (Optional[UploadFile], optional): _description_. Defaults to Form(None).

    Returns:
        _type_: _description_
    """
    if not validate_website(company_url):
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"msg": "Provided URL is not valid"}

    vector_store_id = "vector_store_1234"
    assistant_id = "assistant_id_1234"

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
    """_summary_

    Args:
        company_name (str): _description_

    Returns:
        _type_: _description_
    """
    status = scraping_status.get(company_name)  # Check the status dictionary
    if status is None:
        return {"status": "Not Found", "company_name": company_name}

    return {"status": status, "company_name": company_name}


if __name__ == "__main__":
    uvicorn.run("index:app", port=8000, log_level="info")
