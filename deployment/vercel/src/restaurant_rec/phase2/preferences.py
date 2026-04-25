from typing import List, Optional, Union
from pydantic import BaseModel, Field, field_validator

class UserPreferences(BaseModel):
    location: str = Field(..., description="City or locality (Required)")
    budget_max_inr: Optional[float] = Field(None, description="Max approximate cost for two in INR")
    cuisine: Optional[Union[str, List[str]]] = Field(None, description="Preferred cuisine(s)")
    min_rating: Optional[float] = Field(None, description="Minimum rating required (0-5)")
    extras: Optional[str] = Field(None, description="Free text like 'family-friendly' or 'quick service'")

    @field_validator('cuisine', mode='before')
    @classmethod
    def validate_cuisine(cls, v):
        if isinstance(v, str):
            # Split by comma if it's a comma-separated string
            return [c.strip() for c in v.split(',')]
        return v
