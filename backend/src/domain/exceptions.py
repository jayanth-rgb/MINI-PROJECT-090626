class DomainError(Exception):
    """Base class for all domain errors. Maps to HTTP 500 if no subclass matches."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFoundError(DomainError):
    """Repository lookup miss. Maps to HTTP 404."""

    def __init__(self, entity: str, id_: int):
        super().__init__(f"{entity} with id {id_} not found")
        self.entity = entity
        self.id_ = id_


class ConflictError(DomainError):
    """UNIQUE violation (duplicate grade_code, duplicate design-grade pair). Maps to HTTP 409."""

    pass


class ValidationError(DomainError):
    """Domain rule violation not caught by Pydantic. Maps to HTTP 422."""

    pass
