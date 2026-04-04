"""
SignedData CDS — Companies Brazil Domain Models
Typed Pydantic payload schemas for companies.brazil events.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from cds.vocab import CDSVocab


class CompaniesContentTypes:
    PROFILE  = CDSVocab.COMPANIES_PROFILE_CNPJ
    PARTNERS = CDSVocab.COMPANIES_PARTNERS_CNPJ
    CNAE     = CDSVocab.COMPANIES_CNAE_PROFILE


class CNAECode(BaseModel):
    code: str
    description: str


class CompanyAddress(BaseModel):
    street: str
    number: str
    complement: str | None = None
    neighborhood: str
    zip_code: str
    city: str
    state: str  # UF: "SP", "RJ", etc.


class CompanyProfile(BaseModel):
    """Payload for companies.brazil/profile.cnpj"""
    cnpj: str                       # bare digits: "11222333000144"
    cnpj_formatted: str             # "11.222.333/0001-44"
    company_name: str
    trade_name: str | None = None
    registration_status: Literal["ATIVA", "BAIXADA", "INAPTA", "SUSPENSA", "NULA"]
    registration_date: str          # ISO date
    registration_status_date: str | None = None
    legal_nature_code: str
    legal_nature: str
    size: str                       # "ME", "EPP", "DEMAIS"
    share_capital: float | None = None
    main_cnae: CNAECode
    secondary_cnaes: list[CNAECode] = []
    address: CompanyAddress
    phone: str | None = None
    email: str | None = None
    query_timestamp: str

    @property
    def is_active(self) -> bool:
        return self.registration_status == "ATIVA"


class CompanyPartner(BaseModel):
    name: str
    qualifier: str
    qualifier_code: int
    entry_date: str | None = None
    country: str | None = None
    legal_representative: str | None = None


class CompanyPartners(BaseModel):
    """Payload for companies.brazil/partners.cnpj"""
    cnpj: str
    company_name: str
    partners: list[CompanyPartner]
    query_timestamp: str
