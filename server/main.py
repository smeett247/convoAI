from fastapi import FastAPI, HTTPException
from pocketbase import PocketBase
 
app = FastAPI()
 

pb = PocketBase("http://127.0.0.1:8090") 
 
@app.get("/companies/{company_name}")
async def get_company(company_name: str):
    try:
        companies = pb.collection("companies").get_full_list()
        company = next((c for c in companies if c.company_name == company_name), None)
        if company:
            return {
                "company_name": company.company_name,
                "company_url": company.company_url,
                "logo_provided": bool(company.logo),
                "persona_provided": company.persona
            }
        else:
            raise HTTPException(status_code=404, detail="Company not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/companies")
async def get_all_companies():
    try:
        companies = pb.collection("companies").get_full_list()
        return [{"company_name": company.company_name, "company_url": company.company_url} for company in companies]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
