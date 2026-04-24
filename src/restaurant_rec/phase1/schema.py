from typing import List, Optional
from pydantic import BaseModel, Field

class RestaurantRecord(BaseModel):
    id: str = Field(..., description="Stable SHA256 hash of name + location")
    name: str = Field(..., description="Restaurant name")
    location: str = Field(..., description="Normalized city or locality")
    cuisines: List[str] = Field(default_factory=list, description="List of cuisines")
    rating: Optional[float] = Field(None, description="Float 0-5, parsed from rating string. None if unknown.")
    cost_for_two: Optional[float] = Field(None, description="Approximate cost for two people in INR")
    votes: Optional[int] = Field(0, description="Number of votes/reviews")
    address: Optional[str] = Field(None, description="Full address or locality info")
    raw_features: Optional[str] = Field(None, description="Blob of extra features/info like 'dish_liked' or 'rest_type'")
