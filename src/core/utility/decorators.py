from functools import wraps
from typing import Callable, Any
import traceback
import inspect
from core.utility.responses.models import SuccessResponse, ErrorResponse
from datetime import datetime


def handle_api_exceptions(func: Callable) -> Callable:
    """
    Simple decorator that wraps functions with proper error handling.
    Returns SuccessResponse for successful operations and ErrorResponse for errors.
    Works with both sync and async functions.
    """
    
    def get_error_details(exc: Exception, func_name: str):
        """Extract error details from exception"""
        # Get the traceback
        tb = traceback.extract_tb(exc.__traceback__)
        
        # Find the relevant traceback entry (skip decorator frames)
        relevant_tb = None
        for tb_frame in reversed(tb):
            if 'handle_api_exceptions' not in tb_frame.name and 'wrapper' not in tb_frame.name:
                relevant_tb = tb_frame
                break
        
        if relevant_tb:
            line_number = relevant_tb.lineno
            file_name = relevant_tb.filename.split('/')[-1]
            code_line = relevant_tb.line or "N/A"
        else:
            line_number = 0
            file_name = "unknown"
            code_line = "N/A"
        
        # Create detailed error information
        error_message = f"{type(exc).__name__}: {str(exc)}"
        detailed_errors = [
            f"Exception Type: {type(exc).__name__}",
            f"Error Message: {str(exc)}",
            f"Function: {func_name}",
            f"File: {file_name}",
            f"Line: {line_number}",
            f"Code: {code_line}"
        ]
        
        return error_message, line_number, file_name, detailed_errors
    
    if inspect.iscoroutinefunction(func):
        # Handle async functions
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            try:
                result = await func(*args, **kwargs)
                
                # If result is already a response model, return as-is
                if isinstance(result, (SuccessResponse, ErrorResponse)):
                    return result
                
                # If result is a Pydantic model (like UploadsList), return as-is
                if hasattr(result, 'model_dump') or hasattr(result, 'dict'):
                    return result
                
                # If result is a dict with success info, wrap in SuccessResponse
                if isinstance(result, dict) and "message" in result:
                    return SuccessResponse(
                        message=result.get("message", "Operation successful"),
                        data=result.get("data"),
                        status_code=result.get("status_code", 200),
                        timestamp=datetime.now()
                    )
                
                # For other results, wrap in basic SuccessResponse
                return SuccessResponse(
                    message="Operation successful",
                    data=result,
                    status_code=200,
                    timestamp=datetime.now()
                )
                
            except Exception as e:
                error_message, line_number, file_name, detailed_errors = get_error_details(e, func.__name__)
                
                return ErrorResponse(
                    message=error_message,
                    errors=detailed_errors,
                    line=line_number or 0,
                    file=file_name,
                    status_code=500,
                    timestamp=datetime.now()
                )
        
        return async_wrapper
    else:
        # Handle sync functions
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            try:
                result = func(*args, **kwargs)
                
                # If result is already a response model, return as-is
                if isinstance(result, (SuccessResponse, ErrorResponse)):
                    return result
                
                # If result is a Pydantic model (like UploadsList), return as-is
                if hasattr(result, 'model_dump') or hasattr(result, 'dict'):
                    return result
                
                # If result is a dict with success info, wrap in SuccessResponse
                if isinstance(result, dict) and "message" in result:
                    return SuccessResponse(
                        message=result.get("message", "Operation successful"),
                        data=result.get("data"),
                        status_code=result.get("status_code", 200),
                        timestamp=datetime.now()
                    )
                
                # For other results, wrap in basic SuccessResponse
                return SuccessResponse(
                    message="Operation successful",
                    data=result,
                    status_code=200,
                    timestamp=datetime.now()
                )
                
            except Exception as e:
                error_message, line_number, file_name, detailed_errors = get_error_details(e, func.__name__)
                
                return ErrorResponse(
                    message=error_message,
                    errors=detailed_errors,
                    line=line_number,
                    file=file_name,
                    status_code=500,
                    timestamp=datetime.now()
                )
        
        return sync_wrapper
