import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from database import db, create_document, get_documents
import importlib

app = FastAPI(title="Tenant - Real Estate Management API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- Root & Health --------------------
@app.get("/")
def read_root():
    return {"message": "Tenant API running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Connected & Working"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:20]
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response

# -------------------- Schemas Introspection --------------------
@app.get("/schema")
def get_schema() -> Dict[str, Any]:
    """Expose Pydantic models defined in schemas.py so tools/frontends can build forms dynamically."""
    try:
        schemas_mod = importlib.import_module("schemas")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unable to import schemas: {e}")

    model_names = [
        "Tenant", "Owner", "Property", "Lease", "Sale", "Expense", "Document"
    ]
    out: Dict[str, Any] = {}
    for name in model_names:
        model = getattr(schemas_mod, name, None)
        if model is not None and issubclass(model, BaseModel):
            out[name.lower()] = model.model_json_schema()
    return out

# -------------------- Generic List & Create --------------------
class ListResponse(BaseModel):
    items: List[dict]

VALID_COLLECTIONS = {"tenant","owner","property","lease","sale","expense","document"}

@app.get("/api/{collection}", response_model=ListResponse)
async def list_items(collection: str, limit: int = 25):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    if collection not in VALID_COLLECTIONS:
        raise HTTPException(status_code=404, detail="Collection not found")
    items = get_documents(collection, limit=limit)
    def normalize(doc):
        d = {}
        for k, v in doc.items():
            if k == "_id":
                d[k] = str(v)
            else:
                d[k] = v
        return d
    return {"items": [normalize(i) for i in items]}

@app.post("/api/{collection}")
async def create_item(collection: str, payload: Dict[str, Any]):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    if collection not in VALID_COLLECTIONS:
        raise HTTPException(status_code=404, detail="Collection not found")
    inserted_id = create_document(collection, payload)
    return {"id": inserted_id, "message": "Created"}

# -------------------- File upload & lightweight extraction --------------------
@app.post("/api/upload")
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    related_type: Optional[str] = Form("general"),
    related_id: Optional[str] = Form(None),
):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    filename = file.filename or "uploaded"
    content_type = file.content_type or "application/octet-stream"
    raw = await file.read()

    extracted_text = None

    # Try simple text extraction for CSV/TSV
    try:
        if filename.lower().endswith((".csv", ".tsv")):
            extracted_text = raw.decode(errors="ignore")
    except Exception:
        pass

    # Try simple Excel extraction via note (no heavy parser here)
    if extracted_text is None and filename.lower().endswith((".xlsx", ".xls")):
        extracted_text = "Excel file uploaded (preview disabled)."

    # Naive PDF handling
    if extracted_text is None and filename.lower().endswith(".pdf"):
        extracted_text = "PDF uploaded (text extraction not available in lightweight mode)."

    doc = {
        "title": title or filename,
        "filename": filename,
        "content_type": content_type,
        "tags": [t.strip() for t in (tags.split(",") if tags else []) if t.strip()],
        "related_type": related_type,
        "related_id": related_id,
        "extracted_text": extracted_text,
    }

    inserted_id = create_document("document", doc)
    return {"id": inserted_id, "message": "Uploaded", "preview": extracted_text[:1000] if extracted_text else None}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
