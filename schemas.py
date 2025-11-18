"""
Database Schemas for Tenant (Real Estate Management)

Each Pydantic model represents a collection in MongoDB.
Collection name is the lowercase of the class name (e.g., Tenant -> "tenant").
"""
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, EmailStr
from datetime import date

class Tenant(BaseModel):
    first_name: str = Field(..., description="Tenant first name")
    last_name: str = Field(..., description="Tenant last name")
    email: Optional[EmailStr] = Field(None, description="Contact email")
    phone: Optional[str] = Field(None, description="Contact phone")
    current_property_id: Optional[str] = Field(None, description="Linked property ID if any")
    notes: Optional[str] = Field(None, description="Additional notes")

class Owner(BaseModel):
    first_name: str = Field(..., description="Owner first name")
    last_name: str = Field(..., description="Owner last name")
    email: Optional[EmailStr] = Field(None, description="Contact email")
    phone: Optional[str] = Field(None, description="Contact phone")
    company: Optional[str] = Field(None, description="Company name if applicable")

class Property(BaseModel):
    title: str = Field(..., description="Property title or reference")
    address: str = Field(..., description="Full address")
    city: Optional[str] = Field(None)
    state: Optional[str] = Field(None)
    postal_code: Optional[str] = Field(None)
    country: Optional[str] = Field(None)
    owner_id: Optional[str] = Field(None, description="Linked owner ID")
    type: Optional[Literal['apartment','house','condo','land','office','retail','industrial','other']] = 'apartment'
    bedrooms: Optional[int] = Field(None, ge=0)
    bathrooms: Optional[float] = Field(None, ge=0)
    area_sqft: Optional[float] = Field(None, ge=0)

class Lease(BaseModel):
    tenant_id: str = Field(..., description="Tenant ID")
    property_id: str = Field(..., description="Property ID")
    start_date: date = Field(...)
    end_date: Optional[date] = Field(None)
    monthly_rent: float = Field(..., ge=0)
    deposit: Optional[float] = Field(0, ge=0)
    status: Literal['active','pending','ended'] = 'active'

class Sale(BaseModel):
    property_id: str = Field(...)
    buyer_name: str = Field(...)
    seller_owner_id: Optional[str] = Field(None)
    price: float = Field(..., ge=0)
    date_closed: Optional[date] = None
    status: Literal['listed','under_contract','sold','cancelled'] = 'listed'

class Expense(BaseModel):
    property_id: Optional[str] = Field(None)
    category: Literal['maintenance','tax','utilities','insurance','management','other'] = 'other'
    amount: float = Field(..., ge=0)
    description: Optional[str] = Field(None)
    expense_date: date = Field(...)
    paid: bool = Field(False)

class Document(BaseModel):
    title: str = Field(..., description="Human-friendly title")
    file_id: Optional[str] = Field(None, description="GridFS file id")
    filename: Optional[str] = None
    content_type: Optional[str] = None
    tags: List[str] = []
    related_type: Optional[Literal['tenant','owner','property','lease','sale','expense','general']] = 'general'
    related_id: Optional[str] = None
    extracted_text: Optional[str] = None
    extracted_summary: Optional[str] = None

# The Flames database viewer can read these at /schema
