from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class DateRangeQuery(BaseModel):
    data: Optional[str] = Field(
        None,
        description="Single date DD/MM/YYYY or range DD/MM/YYYY/DD/MM/YYYY",
        example="01/01/2024/31/01/2024",
    )

    @validator("data")
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
        None, description="Start date YYYY-MM-DD", example="2024-01-01"
    )
    data_fim: Optional[str] = Field(
        None, description="End date YYYY-MM-DD", example="2024-01-31"
    )

    @validator("data_inicio", "data_fim")
    def validate_date(cls, v):
        if v is None:
            return v
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")
        return v
