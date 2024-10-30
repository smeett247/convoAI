from db import client as db  # PocketBase client instance
from fastapi import FastAPI, status, Response, Form, UploadFile, BackgroundTasks
from utils import create_vector_store, create_assistant, validate_website, scrap_website
from openai import Client
from dotenv import load_dotenv
from pocketbase.client import ClientResponseError, FileUpload
import uvicorn

load_dotenv()
app = FastAPI()
ai = Client()

# Dictionary to store scraping statuses
scraping_status = {}

# Scraping
async def run_scraping_task(company_url: str, company_name: str):
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
    logo: UploadFile = Form(...),
    additional_websites: str = Form(...)
):
    if not validate_website(company_url):
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"msg": "Provided URL is not valid"}

    vector_store_id = "vector_store_1234"
    assistant_id = "assistant_id_1234"
    logo_binary = await logo.read()

    try:
        db.collection("companies").create(
            {
                "company_name": company_name,
                "company_url": company_url,
                "vector_store_id": vector_store_id,
                "assistant_id": assistant_id,
                "persona": persona,
                "customer_name": customer_name,
                "logo": FileUpload(logo.filename, logo_binary),
                "additional_websites": additional_websites,
            }
        )
        # Set the initial status to "Pending" using the company name as key
        scraping_status[company_name] = "Pending"

        # Start the background task for scraping
        background_tasks.add_task(run_scraping_task, company_url, company_name)

        response.status_code = status.HTTP_201_CREATED
        return {
            "message": "Company saved and scraping started",
            "company_name": company_name
        }
    
    except ClientResponseError as e:
        print(e)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": f"Failed to save company"}
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"error": f"An unexpected error occurred: {str(e)}"}

@app.get("/scraping_status/{company_name}")
async def get_scraping_status(company_name: str):
    status = scraping_status.get(company_name)  # Check the status dictionary
    if status is None:
        return {"status": "Not Found", "company_name": company_name}

    return {"status": status, "company_name": company_name}

if __name__ == "__main__":
    uvicorn.run("index:app", port=8000, log_level="info", reload=True)
