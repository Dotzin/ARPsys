from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime
from passlib.context import CryptContext


class DateRangeQuery(BaseModel):
    data: Optional[str] = Field(
        None,
        description="Single date DD/MM/YYYY or range DD/MM/YYYY/DD/MM/YYYY",
        json_schema_extra={"example": "01/01/2024/31/01/2024"},
    )

    @field_validator("data")
    @classmethod
    def validate_date_format(cls, v):
        if v is None:
            return v
        partes = v.split("/")
        if len(partes) not in [3, 6]:
            raise ValueError(
                "Invalid date format. Use DD/MM/YYYY or DD/MM/YYYY/DD/MM/YYYY"
            )
        try:
            if len(partes) == 3:
                dia, mes, ano = map(int, partes)
                datetime(ano, mes, dia)
            elif len(partes) == 6:
                dia1, mes1, ano1, dia2, mes2, ano2 = map(int, partes)
                datetime(ano1, mes1, dia1)
                datetime(ano2, mes2, dia2)
        except ValueError:
            raise ValueError("Invalid date values")
        return v


class ReportQuery(BaseModel):
    data_inicio: Optional[str] = Field(
        None, description="Start date YYYY-MM-DD", json_schema_extra={"example": "2024-01-01"}
    )
    data_fim: Optional[str] = Field(
        None, description="End date YYYY-MM-DD", json_schema_extra={"example": "2024-01-31"}
    )

    @field_validator("data_inicio", "data_fim")
    @classmethod
    def validate_date(cls, v):
        if v is None:
            return v
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")
        return v


# Password hashing context
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class User(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool = True
    api_session_token: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    api_session_token: Optional[str] = None


class IntegrationCreate(BaseModel):
    integration_type: str  # e.g., 'arpcommerce', 'bearer'
    token_value: str


class TokenRequest(BaseModel):
    token_value: str


class ArpTokenRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    token_value: str = Field(alias="session_cookie")


class BearerTokenRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    token_value: str = Field(alias="bearer_token")


class Integration(BaseModel):
    id: int
    user_id: int
    integration_type: str
    token_value: str
    created_at: datetime
    updated_at: datetime


class SkuNichoInsert(BaseModel):
    sku: str
    nicho: str


class SkuNichoUpdate(BaseModel):
    sku: str
    novo_nicho: str


class SkuNichoDelete(BaseModel):
    sku: str
