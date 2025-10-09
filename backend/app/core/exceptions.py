class ARPSysException(Exception):
    """Base exception for ARPSys application."""
    pass


class DatabaseException(ARPSysException):
    """Exception raised for database-related errors."""
    pass


class APIException(ARPSysException):
    """Exception raised for external API errors."""
    pass


class ValidationException(ARPSysException):
    """Exception raised for input validation errors."""
    pass


class ReportGenerationException(ARPSysException):
    """Exception raised when report generation fails."""
    pass


class FileProcessingException(ARPSysException):
    """Exception raised for file processing errors."""
    pass


class AuthenticationException(ARPSysException):
    """Exception raised for authentication errors."""
    pass


class UserNotFoundException(ARPSysException):
    """Exception raised when user is not found."""
    pass


class TokenException(ARPSysException):
    """Exception raised for token-related errors."""
    pass
