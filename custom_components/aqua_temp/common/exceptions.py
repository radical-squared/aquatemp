class OperationFailedException(Exception):
    operation: str
    error: str | dict
    value: str

    def __init__(self, operation: str, value: str, error: str | dict):
        self.operation = operation
        self.error = error
        self.value = value

    def __str__(self):
        result = f"Failed to set value of {self.operation} to {self.value}, Error: {self.error}"

        return result


class LoginError(Exception):
    def __init__(self):
        self.error = "Failed to login"
