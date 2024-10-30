from openai import Client
import zon as z
import re


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


def scrap_website(company_url: str):
    """Recursively Scrap the URL provided

    Args:
        company_url (str): URL of the company provided
    """
    pass


def validate_website(website: str):
    url_validator = z.string().url()
    try:
        url_validator.validate(website)
        return True
    except:
        return False
