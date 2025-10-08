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
