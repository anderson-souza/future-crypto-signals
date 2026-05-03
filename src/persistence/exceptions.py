class PersistenceError(Exception):
    def __init__(self, operation: str, message: str = "") -> None:
        self.operation = operation
        super().__init__(message or f"Persistence failed during '{operation}'")
