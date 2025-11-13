from pydantic import BaseModel, Field, field_validator, ValidationError
from typing import Literal, Optional, List, Any, Dict

SortType = Literal["PRICE_ASC", "PRICE_DESC", "BEST_SELLERS", "RELEVANCE"]
Region = str  # Expect two-letter country code like "US", "VN"

class InputModel(BaseModel):
    keyword: Optional[str] = Field(
        default=None, description="Search keyword for TikTok Shop listings"
    )
    isTrending: bool = Field(default=False, description="Return trending items only")
    region: Optional[Region] = Field(
        default=None, description="Two-letter ISO country code (e.g., US, VN)"
    )
    sortType: SortType = Field(
        default="RELEVANCE",
        description="Sorting behavior for results",
    )
    limit: int = Field(
        default=50, ge=1, le=2000, description="Maximum number of products to fetch"
    )
    startUrls: Optional[List[str]] = Field(
        default=None, description="Optional explicit product/listing URLs to parse"
    )

    @field_validator("region")
    @classmethod
    def validate_region(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not isinstance(v, str) or len(v) != 2 or not v.isalpha():
            raise ValueError("region must be a two-letter ISO country code")
        return v.upper()

    @field_validator("keyword")
    @classmethod
    def validate_keyword(cls, v: Optional[str], info: Any) -> Optional[str]:
        # If no startUrls provided, keyword must be present (unless isTrending)
        data: Dict[str, Any] = info.data if hasattr(info, "data") else {}
        start_urls = data.get("startUrls")
        is_trending = data.get("isTrending", False)
        if not start_urls and not is_trending and not v:
            raise ValueError("keyword is required when startUrls is not provided and isTrending is False")
        return v.strip() if isinstance(v, str) else v

def validate_input(payload: dict) -> InputModel:
    """
    Validate raw JSON payload into InputModel. Raises ValidationError on failure.
    """
    try:
        return InputModel.model_validate(payload or {})
    except ValidationError as e:
        # Re-raise with clean error message
        raise ValidationError(e.errors()) from None