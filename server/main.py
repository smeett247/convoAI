# main.py
from fastapi import (
    FastAPI,
    UploadFile,
    File,
    Depends,
    HTTPException,
    Form,
    BackgroundTasks,
)
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from server.migrate import Company, Base
from database import get_db, engine
import openai
import os
from dotenv import load_dotenv
from typing import Optional, List
from PIL import Image
import io
import validators
from docx import Document
from pptx import Presentation
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import PyPDF2
import markdown
import pdfkit
from bs4 import BeautifulSoup
import time
import logging
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from urllib.parse import urlparse, urlsplit, urljoin
import subprocess
from docx2pdf import convert
from pptxtopdf import convert
from scrapper import (
    scrape_entire_website,
    convert_markdown_files_to_pdf,
    convert_attachments_to_pdf,
)

scraping_status = {}


def convert_docx_to_pdf(docx_path: str, pdf_path: str):
    """Convert DOCX to PDF."""
    convert(docx_path, pdf_path)


def convert_pptx_to_pdf(pptx_path: str, pdf_path: str):
    """Convert PPTX to PDF."""
    convert(pptx_path, pdf_path)


# Initialize logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI()


# Create tables on startup
@app.on_event("startup")
def create_tables():
    Base.metadata.create_all(bind=engine)


def upload_files_to_vector_store(company_name: str, pdf_files: List[str]):
    """Create a vector store for the company and upload PDF files to it."""
    vector_store = client.beta.vector_stores.create(name=company_name)
    file_streams = [open(pdf_path, "rb") for pdf_path in pdf_files]
    try:
        client.beta.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store.id, files=file_streams
        )
    finally:
        for stream in file_streams:
            stream.close()

    return vector_store.id


def create_assistant(vector_store_id: str, company_name: str):
    """Create an assistant using the vector store."""
    assistant = client.beta.assistants.create(
        name=company_name,
        instructions="You are a helpful product support assistant and you answer questions based on the files provided.",
        model="gpt-4o-mini",
        tools=[{"type": "file_search"}],
        tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}},
    )
    return assistant.id


def convert_markdown_to_pdf(markdown_path: str) -> str:
    """Convert a Markdown file to PDF."""
    try:
        with open(markdown_path, "r", encoding="utf-8") as f:
            text = f.read()
            html_content = markdown.markdown(text)

        pdf_path = markdown_path.replace(".md", ".pdf")
        css = """
        <style>
            body { font-family: 'Calibri', sans-serif; }
            h1, h2, h3 { color: #2e3b4e; }
            p { line-height: 1.6; }
        </style>
        """
        full_html = css + html_content
        pdfkit.from_string(full_html, pdf_path, options={"quiet": ""})
        return pdf_path
    except Exception as e:
        logger.error(f"Error converting {markdown_path} to PDF: {e}")
        raise


def convert_txt_to_pdf(txt_path: str, pdf_path: str):
    """Convert a TXT file to PDF."""
    pdf_canvas = canvas.Canvas(pdf_path, pagesize=letter)
    with open(txt_path, "r") as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            pdf_canvas.drawString(100, 750 - i * 15, line.strip())
            if i % 50 == 0:
                pdf_canvas.showPage()
    pdf_canvas.save()


def process_files(file_paths: List[str]) -> List[str]:
    """Process files and return a list of converted PDF paths."""
    pdf_files = []
    for path in file_paths:
        if path.endswith(".pdf"):
            pdf_files.append(path)
        elif path.endswith(".docx"):
            pdf_path = path.replace(".docx", ".pdf")
            convert_docx_to_pdf(path, pdf_path)
            pdf_files.append(pdf_path)
        elif path.endswith(".pptx"):
            pdf_path = path.replace(".pptx", ".pdf")
            convert_pptx_to_pdf(path, pdf_path)
            pdf_files.append(pdf_path)
        elif path.endswith(".txt"):
            pdf_path = path.replace(".txt", ".pdf")
            convert_txt_to_pdf(path, pdf_path)
            pdf_files.append(pdf_path)
        elif path.endswith(".md"):
            pdf_path = path.replace(".md", ".pdf")
            convert_txt_to_pdf(path, pdf_path)
            pdf_files.append(pdf_path)
    return pdf_files


def validate_image(logo: UploadFile) -> bytes:
    """Validate if the uploaded file is a valid image and return its binary content."""
    try:
        if logo.content_type not in [
            "image/jpeg",
            "image/png",
            "image/jpg",
            "image/bmp",
            "image/tiff",
            "image/webp",
            "image/x-tiff",
        ]:
            raise HTTPException(
                status_code=400,
                detail="Only JPG, JPEG, PNG, BMP, TIFF, x-TIFF, and WEBP images are allowed.",
            )

        content = logo.file.read()
        Image.open(io.BytesIO(content)).verify()
        return content
    except Exception:
        raise HTTPException(
            status_code=400, detail="Invalid image format. Please upload a valid image."
        )


#####################################################################################################################################################


@app.post("/create-company/")
async def create_company(
    company_name: str = Form(...),
    company_url: str = Form(...),
    logo: Optional[UploadFile] = File(None),
    additional_websites: Optional[List[str]] = Form(None),
    persona: str = Form(...),
    attachments: Optional[List[UploadFile]] = File(None),
    customer_name: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),  # For background processing
):

    if not company_url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="Invalid URL format.")

    if db.query(Company).filter(Company.company_name == company_name).first():
        raise HTTPException(status_code=400, detail="Company already exists.")

    start_time = time.time()

    # Validate and store the logo (if provided)
    logo_data = validate_image(logo) if logo else None

    # Save uploaded attachments
    pdf_files = []
    if attachments:
        upload_folder = "uploads/"
        os.makedirs(upload_folder, exist_ok=True)
        for attachment in attachments:
            file_path = os.path.join(upload_folder, attachment.filename)
            with open(file_path, "wb") as f:
                f.write(attachment.file.read())
            pdf_files.append(file_path)

    pdf_files = process_files(pdf_files)

    # Generate vector store and assistant IDs
    vector_store_id = upload_files_to_vector_store(company_name, pdf_files)
    assistant_id = create_assistant(vector_store_id, company_name)

    # Create a new company record with relevant fields
    new_company = Company(
        company_name=company_name,
        company_url=company_url,
        vector_store_id=vector_store_id,
        assistant_id=assistant_id,
        persona=persona,
        customer_name=customer_name,
        logo=logo_data,  # Store logo data here
    )
    db.add(new_company)
    db.commit()  # Commit the changes to the database

    # Start website scraping in the background
    background_tasks.add_task(scrape_entire_website, company_url, company_name)

    elapsed_time = time.time() - start_time
    formatted_time = f"{elapsed_time:.2f} seconds"

    print(
        f"Company created successfully and scraping has started. Time taken: {formatted_time}"
    )

    return {
        "message": f"Company created successfully and scraping has started. Time taken: {formatted_time}"
    }


def scrape_website(company_name: str, company_url: str):
    # Simulate scraping with time delay
    scraping_status[company_name] = "Scraping in progress"

    # Simulate scraping with a delay (replace this with actual scraping logic)
    time.sleep(5)

    # Update status to "Scraping completed" after scraping finishes
    scraping_status[company_name] = "Scraping completed"


##########################################################################################################################


@app.get("/scraping-status/{company_name}")
def get_scraping_status(company_name: str, db: Session = Depends(get_db)):
    # Check if the company exists in the database
    existing_company = (
        db.query(Company).filter(Company.company_name == company_name).first()
    )
    if not existing_company:
        return {"company_name": company_name, "scraping_status": "Company not found"}

    # Return the current status from the dictionary, or "Scraping completed" if already in database
    status = scraping_status.get(company_name, "Scraping completed")
    return {"company_name": company_name, "scraping_status": status}


########################################################################################################


@app.get("/companies/{company_name}")
def get_company(company_name: str, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.company_name == company_name).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found.")

    return {
        "company_name": company.company_name,
        "company_url": company.company_url,
        "logo_provided": bool(company.logo),
        "persona_provided": company.persona,
    }
