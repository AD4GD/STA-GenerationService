from typing import Optional

from pydantic import BaseModel, Field


class Pilot(BaseModel):
    name: str
    description: Optional[str] = None
    custom_endpoint: Optional[str] = Field(default=None, examples=[None])
    graphs: list[str]

    class Config:
        from_attributes = True


class PilotResponse(Pilot):
    rootURL: str
    swaggerURL: str
