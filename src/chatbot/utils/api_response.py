from typing import Any, Optional
from pydantic import BaseModel

class ApiResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None
    data: Optional[Any] = None
    meta: Optional[dict] = None

    @staticmethod
    def success_response(
        data: Any = None,
        message: str = "Request successful",
        meta: dict | None = None
    ):
        return {
            "success": True,
            "message": message,
            "data": data,
            "meta": meta
        }