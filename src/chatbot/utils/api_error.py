from fastapi import HTTPException, status

class ApiError(HTTPException):
    def __init__(
        self,
        status_code: int,
        message: str,
        errors: list | None = None
    ):
        super().__init__(
            status_code=status_code,
            detail={
                "success": False,
                "message": message,
                "errors": errors
            }
        )

class BadRequestError(ApiError):
    def __init__(self, message="Bad request", errors=None):
        super().__init__(status.HTTP_400_BAD_REQUEST, message, errors)

class UnauthorizedError(ApiError):
    def __init__(self, message="Unauthorized"):
        super().__init__(status.HTTP_401_UNAUTHORIZED, message)

class ForbiddenError(ApiError):
    def __init__(self, message="Forbidden"):
        super().__init__(status.HTTP_403_FORBIDDEN, message)

class NotFoundError(ApiError):
    def __init__(self, message="Resource not found"):
        super().__init__(status.HTTP_404_NOT_FOUND, message)

class InternalServerError(ApiError):
    def __init__(self, message="Internal server error"):
        super().__init__(status.HTTP_500_INTERNAL_SERVER_ERROR, message)