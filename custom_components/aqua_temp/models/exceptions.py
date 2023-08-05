from typing import Any


class OperationFailedException(Exception):
    operation: str
    error: str | dict
    value: str

    def __init__(self, operation: str, value: Any, error: str | dict):
        self.operation = operation
        self.error = error
        self.value = value

    def __str__(self):
        result = f"Failed to set value of {self.operation} to {self.value}, Error: {self.error}"

        return result


class LoginError(Exception):
    def __str__(self):
        result = "Failed to login"

        return result


class InvalidTokenError(Exception):
    flow: str

    def __init__(self, flow: str):
        self.flow = flow

    def __str__(self):
        result = f"Invalid token, Flow: {self.flow}"

        return result
