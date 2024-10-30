from openai import Client
import zon as z
from markdown_pdf import MarkdownPdf, Section
import os


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


def convert_markdown_to_pdf(path: str, output_dir: str = "temp/pdf"):
    """Convert a Markdown file to PDF format with TOC and CSS styling.

    Args:
        path (str): Path to the Markdown file.
        output_dir (str): Directory to save the generated PDF file. Defaults to "temp/pdf".
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


def scrap_website(company_url: str):
    """Recursively Scrap the URL provided

    Args:
        company_url (str): URL of the company provided
    """
    pass


def validate_website(website: str) -> bool:
    """

    Args:
        website (str): Website url that needs to be validated

    Returns:
        bool : Weather the provided string is a URL or not
    """
    url_validator = z.string().url()
    try:
        url_validator.validate(website)
        return True
    except:
        return False


if __name__ == "__main__":
    convert_markdown_to_pdf("./temp/markdown/fathom.md")
