"""Team schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TeamCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=2, max_length=160)
    cnpj: str | None = Field(default=None, max_length=18)
    razao_social: str | None = Field(default=None, max_length=200)
    responsavel: str = Field(min_length=2, max_length=120)
    responsavel_cpf: str = Field(min_length=11, max_length=14)
    responsavel_email: str = Field(min_length=5, max_length=255)
    responsavel_password: str = Field(min_length=6, max_length=128)


class TeamUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=2, max_length=160)
    cnpj: str | None = Field(default=None, max_length=18)
    razao_social: str | None = Field(default=None, max_length=200)
    responsavel: str | None = Field(default=None, min_length=2, max_length=120)
    responsavel_cpf: str | None = Field(default=None, min_length=11, max_length=14)
    responsavel_email: str | None = Field(default=None, max_length=255)
    responsavel_password: str | None = Field(default=None, max_length=128)


class TeamRead(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    id: int
    area_id: int
    name: str
    cnpj: str | None = None
    razao_social: str | None = None
    responsavel: str
    responsavel_cpf: str
    responsavel_email: str | None = None
    deleted_at: datetime | None = None
    created_at: datetime
