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
    scraping_status,
    session_manager,
    upload_pdf_to_vector_store
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


async def run_scraping_task(company_name: str, websites: list):
    """Runs the scraping task for the specified company URL.

    This function updates the scraping status for the company, performs the website scraping,
    and handles any exceptions that may occur during the process.

    Args:
        company_url (str): The URL of the company's website to scrape.
        company_name (str): The name of the company for tracking status.

    Returns:
        None
    """
    global total_scraped_companies  # Use the global variable
    for url in websites:
        try:
            # Initialize status for each website
            scraping_status[f"{company_name}_{url}"] = {
                "status": "In Progress",
                "start_time": datetime.now(),
                "elapsed": 0
            }
            
            end_time = datetime.now() + timedelta(minutes=2)

            while datetime.now() < end_time:
                # Here, you can call your scrap_website function to perform the scraping
                scrap_website(url, company_name)
                scraping_status[f"{company_name}_{url}"]["elapsed"] = (datetime.now() - scraping_status[f"{company_name}_{url}"]["start_time"]).total_seconds()
                # Sleep for a short duration to prevent busy waiting
                await asyncio.sleep(1)  # Adjust sleep duration if needed
            
            # Update status as "Completed"
            scraping_status[f"{company_name}_{url}"]["status"] = "Completed"
            
            # Increment the total scraped companies count
            total_scraped_companies += 1

        except Exception as e:
            # Capture any unexpected error
            scraping_status[f"{company_name}_{url}"]["status"] = f"Failed: {str(e)}"
            scraping_status[f"{company_name}_{url}"]["elapsed"] = (datetime.now() - scraping_status[f"{company_name}_{url}"]["start_time"]).total_seconds()

origins = ["http://localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

scraping_status = dict()
session_manager = dict()


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
    print("++++++Logo+++++++")
    print(logo)
    print("+++++++++++++")
    
    print("++++++Attachments+++++++")
    print(attachments)
    print("+++++++++++++")
    
    company_name = company_name.lower().strip().replace(" ", "_")
    if not validate_website(company_url):
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"msg": "Provided URL is not valid"}


    vector_store_id = "vid_123"
    assistant_id = "aid_123"
    if logo:
        logo_binary = await logo.read()
        logo = FileUpload(logo.filename, logo_binary)
    else:
        logo = None

    # Check if the company has already been scraped
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

        # Prepare list of websites to scrape
        websites_to_scrape = [company_url]
        print(websites_to_scrape)
        if additional_websites:
            websites_to_scrape.extend(additional_websites.split(","))  # Split additional websites by comma
        print(websites_to_scrape)

        # Initialize status for each website
        for url in websites_to_scrape:
            scraping_status[f"{company_name}_{url}"] = {"status": "Pending", "elapsed": 0}

        # Start scraping in the background
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

    # Prepare response data without start_time for each website
    response_data = {
        "total_scraped": total_scraped_companies,  # Include total companies scraped
        "companies": {}
    }
    
    overall_elapsed = 0
    for company_url, status_data in statuses.items():
        if status_data["status"] == "In Progress":
            status_data["elapsed"] = (datetime.now() - status_data["start_time"]).total_seconds()
        
        # Add status and elapsed time for each URL
        response_data["companies"][company_url] = {
            "status": status_data["status"],
            "elapsed": status_data["elapsed"]
        }

        # Sum overall elapsed time for all URLs being scraped
        overall_elapsed += status_data["elapsed"]

    response_data["overall_elapsed"] = overall_elapsed  # Include overall elapsed time

    return response_data

if __name__ == "__main__":
    uvicorn.run("index:app", port=8000, log_level="info")
