from db import client as db  # PocketBase client instance
from fastapi import FastAPI, status, Response, Form, UploadFile, BackgroundTasks, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from utils import create_vector_store, create_assistant, scrap_website
from openai import Client
from dotenv import load_dotenv
from pocketbase.client import ClientResponseError, FileUpload
from typing import Optional
from datetime import datetime, timedelta
import uvicorn
import asyncio

load_dotenv()
app = FastAPI()
ai = Client()

# Dictionary to store scraping status and progress
scraping_status = {}
total_scraped_companies = 0  # Global variable to track total companies scraped

async def run_scraping_task(company_name: str, websites: list):
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
    # if not validate_website(company_url):
    #     response.status_code = status.HTTP_400_BAD_REQUEST
    #     return {"msg": "Provided URL is not valid"}


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

    # Save company to the database
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
    # Filter status for entries related to the requested company
    statuses = {name: data for name, data in scraping_status.items() if name.startswith(company_name)}

    if not statuses:
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
