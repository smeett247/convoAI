from openai import Client
from markdown_pdf import MarkdownPdf, Section
import os
import sys
import logging
import subprocess
import openai
from urllib.parse import urlparse, urlsplit, urljoin
from bs4 import BeautifulSoup
import httpx
from dotenv import load_dotenv
import re

load_dotenv()


logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.DEBUG)
stdout_handler.setFormatter(formatter)

file_handler = logging.FileHandler("scraping.log")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stdout_handler)

# Variables for file management
attachment_extensions = ["pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx"]
markdown_files = []
attachment_files = []

load_dotenv()

def create_vector_store(client: Client, company_name: str):
    """Create a vector store for company

    Args:
        client (Client): OpenAI Client
        company_name (str): Name of the company for which vector store will be generated (will be used to name the vector store)
    """
    vector_store = client.beta.vector_stores.create(name=company_name)
    return vector_store.id


def create_assistant(client: Client, vector_store_id: str, company_name: str):
    """Create assistant of a company using it's previously generated vector store and company name.

    Args:
        client (Client): OpenAI Client
        vector_store_id (str): Vector Store ID generated for the company
        company_name (str): Name of the company for which assistant needs to be generated

    Returns:
        str: Assistant ID of the generated assistant for company
    """
    assistant = client.beta.assistants.create(
        name=company_name,
        instructions=f"You are a helpful product support assistant for the company {company_name} and you answer questions based on the files provided.",
        model="gpt-4o-mini",
        tools=[{"type": "file_search"}],
        tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}},
    )
    return assistant.id


def save_extensions(
    url: str, content: bytes, folder: str, extensions: list[str], company_name: str
):
    """Saves content to a file if the URL's extension is in the specified list.

    Args:
        url (str): The URL of the file.
        content (bytes): The content to save.
        folder (str): The folder where the file will be saved.
        extensions (list[str]): List of allowed file extensions.
        company_name (str): The company name for folder organization.

    Returns:
        None
    """

    folder_dir = os.path.join(os.getcwd(), folder, company_name)
    os.makedirs(folder_dir, exist_ok=True)

    file_extension = url.split(".")[-1].lower()
    if file_extension in extensions:
        file_name = url.split("/")[-1]
        file_path = os.path.join(folder_dir, file_name)

        if os.path.exists(file_path):
            base_name, ext = os.path.splitext(file_name)
            counter = 1
            while os.path.exists(file_path):
                file_path = os.path.join(folder_dir, f"{base_name}_{counter}{ext}")
                counter += 1

        with open(file_path, "wb") as file:
            file.write(content)
        logger.info(f"Downloaded attachment {file_path}")

        attachment_files.append(file_path)


def generate_page_report(url: str, content: bytes, company_name: str):
    """Generates a Markdown report from webpage content.

    Args:
        url (str): The webpage URL.
        content (bytes): HTML content of the webpage.
        company_name (str): The company name for report organization.

    Returns:
        None
    """

    soup = BeautifulSoup(content, "lxml")
    title = (
        soup.title.string.strip()
        if soup.title and soup.title.string
        else "No Title Found"
    )
    description_meta = soup.find("meta", attrs={"name": "description"})
    description = (
        description_meta["content"].strip()
        if description_meta and description_meta.get("content")
        else "No Description Found"
    )
    body_text = "\n".join([p.get_text(strip=True) for p in soup.find_all("p")])

    report_content = f"""# {title}

##### URL: [{url}]({url})

**Description**: {description}

**Body Text**:

{body_text}

---

"""

    url_domain = urlsplit(url).netloc
    if not url_domain:
        logger.error("Invalid URL provided, cannot generate report filename.")
        return

    domain_name = (
        url_domain.split(".")[-2]
        if len(url_domain.split(".")) > 2
        else url_domain.split(".")[0]
    )
    reports_dir = os.path.join(os.getcwd(), "temp", "markdown")
    os.makedirs(reports_dir, exist_ok=True)

    report_filename_md = f"{domain_name}.md"
    report_filepath_md = os.path.join(reports_dir, report_filename_md)

    with open(
        report_filepath_md, "a", encoding="utf-8", errors="ignore"
    ) as report_file:
        report_file.write(report_content)

    logger.info(f"Report for {url} has been appended to {report_filename_md}")

    if report_filepath_md not in markdown_files:
        markdown_files.append(report_filepath_md)


def scrape_entire_website(start_url: str, company_name: str, max_iterations=10):
    """
    Scrapes a website starting from the given URL.

    Iteratively fetches pages and saves attachments if their URLs match specified extensions.
    Generates a report for HTML content found on the pages.

    Args:
        start_url (str): The starting URL for scraping.
        company_name (str): The name of the company for organizing reports.
        max_iterations (int, optional): Maximum number of pages to scrape. Defaults to 10.

    Returns:
        None
    """

    parsed_start_url = urlparse(start_url)
    base_domain = parsed_start_url.netloc

    urls_to_scrape = [start_url]
    scraped_urls = set()
    iteration_count = 0

    while urls_to_scrape:
        if iteration_count >= max_iterations:
            logger.info(
                f"Maximum iteration count of {max_iterations} reached. Stopping scraping."
            )
            break

        url = urls_to_scrape.pop(0)
        if url in scraped_urls:
            logger.debug(f"URL already scraped: {url}")
            continue

        logger.info(f"Fetching URL: {url}")
        try:
            r = httpx.get(url, verify=False, timeout=10)
            r.raise_for_status()
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            continue

        scraped_urls.add(url)
        iteration_count += 1

        content_type = r.headers.get("Content-Type", "").lower()
        if any(url.lower().endswith(f".{ext}") for ext in attachment_extensions):
            save_extensions(
                url, r.content, "attachments", attachment_extensions, company_name
            )
            continue

        if "text/html" in content_type:
            generate_page_report(url, r.content, company_name)
        else:
            logger.info(f"Non-HTML content at {url}, skipping parsing.")
            continue

        soup = BeautifulSoup(r.content, "lxml")
        new_urls = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            joined_url = urljoin(url, href)
            parsed_joined_url = urlparse(joined_url)

            if (
                parsed_joined_url.netloc == base_domain
                and joined_url not in scraped_urls
                and joined_url not in urls_to_scrape
            ):
                new_urls.add(joined_url)

        logger.info(f"Found {len(new_urls)} new URLs on {url}.")
        urls_to_scrape.extend(new_urls)


def convert_markdown_to_pdf(path: str, output_dir: str = "temp/pdf"):
    """
    Convert a Markdown file to PDF format with a Table of Contents and CSS styling.

    Args:
        path (str): Path to the Markdown file to be converted.
        output_dir (str): Directory where the generated PDF file will be saved.
                          Defaults to "temp/pdf".
    """

    pdf = MarkdownPdf(toc_level=2)

    with open(path, "r", encoding="utf-8") as file:
        content = file.read()

    pdf.add_section(Section(content))
    pdf.meta["author"] = "NotTheRightGuy"

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(
        output_dir, os.path.splitext(os.path.basename(path))[0] + ".pdf"
    )

    pdf.save(output_path)


def convert_attachments_to_pdf():
    """
    Convert various attachment files (DOC, DOCX, PPT, PPTX) to PDF format.

        This function processes a set of attachment file paths, converting supported
        file types to PDF using LibreOffice. If a file is already in PDF format,
        it logs this information. Unsupported file types are also logged.

        Args:
            None

        Returns:
            None
    """
    for file_path in set(attachment_files):
        try:
            file_extension = file_path.split(".")[-1].lower()
            pdf_file_path = file_path.rsplit(".", 1)[0] + ".pdf"

            if file_extension in ["doc", "docx", "pptx", "ppt"]:
                result = subprocess.run(
                    [
                        "libreoffice",
                        "--headless",
                        "--convert-to",
                        "pdf",
                        "--outdir",
                        os.path.dirname(file_path),
                        file_path,
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                if result.returncode == 0:
                    logger.info(f"Converted {file_path} to PDF at {pdf_file_path}")
                else:
                    logger.error(
                        f"Failed to convert {file_path} to PDF. LibreOffice error: {result.stderr.decode()}"
                    )
            elif file_extension == "pdf":
                logger.info(f"Attachment {file_path} is already a PDF.")
            else:
                logger.warning(
                    f"Cannot convert {file_path} to PDF. Unsupported file type."
                )

        except Exception as e:
            logger.error(f"Error converting attachment {file_path} to PDF: {e}")


def scrap_website(company_url: str, company_name: str):
    """Recursively scrape the specified company URL and convert results.

    Args:
        company_url (str): The URL of the company to be scraped.
        company_name (str): The name of the company for reporting purposes.

    Returns:
        None
    """
    max_iterations_input = 200

    if not max_iterations_input:
        max_iterations = 1000
    else:
        try:
            max_iterations = int(max_iterations_input)
        except ValueError:
            logger.error("Invalid input for maximum iterations. Please enter a number.")
            sys.exit(1)

    scrape_entire_website(company_url, company_name, max_iterations)

    logging.info("Scraping completed.")
    for md in markdown_files:
        convert_markdown_to_pdf(md)

    logging.info("Markdown files converted to PDFs.")
    logging.info("Attachments converted to PDFs.")
    logging.info("All conversions completed.")


import re


def validate_website(website: str) -> bool:
    """
    Validates if the given website URL is in a valid format.

    Args:
        website (str): Website URL that needs to be validated.

    Returns:
        bool: Whether the provided string is a valid URL or not.
    """
    url_pattern = re.compile(
        r"^(https?://)?"  # Optional http or https
        r"([a-zA-Z0-9-]+\.)+"  # Domain name segments
        r"[a-zA-Z]{2,}"  # Top-level domain
        r"(/[a-zA-Z0-9._/?&=-]*)*$",  # Optional path/query
        re.IGNORECASE,
    )
    return bool(url_pattern.match(website))


def extract_sentences(text):
    """
    Extracts sentences from the given text, returning a list of individual
    sentences and any remaining text that doesn't end with a sentence-ending punctuation.

    Args:
        text (str): The input text to extract sentences from.

    Returns:
        tuple: A tuple containing:
            - list: A list of sentences ending with '.', '!', or '?'.
            - str: Remaining text that does not end with '.', '!', or '?'.
    """
    sentence_end_pattern = re.compile(r"([^.!?]*[.!?])", re.M)
    sentences = sentence_end_pattern.findall(text)
    buffer = sentence_end_pattern.sub("", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    buffer = buffer.strip()
    return sentences, buffer


def process_stream_event(event, assistant_reply_parts, sentence_queue, buffer_dict):
    """
    Processes an event from the OpenAI assistant stream, extracting and queuing
    sentences while handling any additional buffering and special characters.

    Args:
        event (openai.types.beta.assistant_stream_event.ThreadMessageDelta):
            The incoming event message to process, expected to contain text data.
        assistant_reply_parts (list): A list accumulating cleaned text parts
            from the assistant's replies.
        sentence_queue (Queue): A queue where processed and complete sentences are added.
        buffer_dict (dict): A dictionary holding the "buffer" key, where partially
            complete sentence fragments are stored until fully formed.

    """
    if isinstance(event, openai.types.beta.assistant_stream_event.ThreadMessageDelta):
        if isinstance(
            event.data.delta.content[0],
            openai.types.beta.threads.text_delta_block.TextDeltaBlock,
        ):
            new_content = event.data.delta.content[0].text.value
            cleaned_text = ""
            i = 0
            while i < len(new_content):
                if new_content[i] != "【":
                    cleaned_text += new_content[i]
                elif new_content[i] == "【":
                    i += 1
                    while i < len(new_content) and new_content[i] != "】":
                        i += 1
                i += 1

            if cleaned_text:
                assistant_reply_parts.append(cleaned_text)
                buffer_dict["buffer"] += cleaned_text
                sentences, buffer_dict["buffer"] = extract_sentences(
                    buffer_dict["buffer"]
                )
                for sentence in sentences:
                    sentence_queue.put(sentence)
