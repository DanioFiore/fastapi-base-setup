from functools import wraps
from datetime import datetime
from typing import Callable, Any, Type, Optional, Dict
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session
from .responses.models import SuccessResponse, ErrorResponse


def handle_exceptions(
    success_response_class: Type[SuccessResponse], 
    error_response_class: Type[ErrorResponse],
    custom_error_messages: Optional[Dict[Type[Exception], str]] = None
):
    """
    General decorator for handling try/except with automatic success/error response generation.
    Works with any API endpoint and any SuccessResponse/ErrorResponse models.
    
    Args:
        success_response_class: The SuccessResponse model class to use for successful operations
        error_response_class: The ErrorResponse model class to use for failed operations
        custom_error_messages: Optional dict mapping exception types to custom error messages
    
    Usage:
        @handle_exceptions(ProductCreateSuccessResponse, ProductCreateErrorResponse)
        def create_product(payload, session):
            # Your business logic here
            return product_data  # This will be wrapped in success_response_class
            
        @handle_exceptions(
            OrderSuccessResponse, 
            OrderErrorResponse,
            custom_error_messages={ValueError: "Invalid order data"}
        )
        def process_order(order_data):
            # Your business logic here
            return order_result
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                # Execute the original function
                result = func(*args, **kwargs)
                
                # If the result is already a response model, return it as-is
                if isinstance(result, (SuccessResponse, ErrorResponse)):
                    return result
                
                # Otherwise, wrap the result in the success response
                return success_response_class(
                    data=result,
                    timestamp=datetime.now(),
                    status_code=200
                )
                
            except IntegrityError as e:
                # Handle database integrity errors (unique constraints, etc.)
                session = _get_session_from_args(*args, **kwargs)
                if session:
                    session.rollback()
                
                error_message = "Database constraint violation"
                if custom_error_messages and IntegrityError in custom_error_messages:
                    error_message = custom_error_messages[IntegrityError]
                
                return error_response_class(
                    message=error_message,
                    errors=["Constraint violation - data already exists or invalid"],
                    line=0,
                    file=func.__module__.split('.')[-1] + '.py',
                    timestamp=datetime.now(),
                    status_code=400
                )
                
            except ValueError as e:
                # Handle validation errors
                error_message = "Validation error"
                if custom_error_messages and ValueError in custom_error_messages:
                    error_message = custom_error_messages[ValueError]
                    
                return error_response_class(
                    message=error_message,
                    errors=[str(e)],
                    line=0,
                    file=func.__module__.split('.')[-1] + '.py',
                    timestamp=datetime.now(),
                    status_code=400
                )
                
            except Exception as e:
                # Handle all other exceptions
                session = _get_session_from_args(*args, **kwargs)
                if session:
                    session.rollback()
                
                error_message = "Internal server error"
                if custom_error_messages and type(e) in custom_error_messages:
                    error_message = custom_error_messages[type(e)]
                
                return error_response_class(
                    message=error_message,
                    errors=[str(e)],
                    line=0,
                    file=func.__module__.split('.')[-1] + '.py',
                    timestamp=datetime.now(),
                    status_code=500
                )
        return wrapper
    return decorator


def handle_not_found(
    error_response_class: Type[ErrorResponse], 
    not_found_message: str = "Resource not found"
):
    """
    General decorator for handling "not found" scenarios for any resource type.
    Use this in combination with handle_exceptions for better error handling.
    
    Args:
        error_response_class: The ErrorResponse model class to use
        not_found_message: Custom message for not found scenarios
    
    Usage:
        @handle_exceptions(ProductGetSuccessResponse, ProductGetErrorResponse)
        @handle_not_found(ProductGetErrorResponse, "Product not found")
        def get_product(product_id, session):
            product = session.get(Product, product_id)
            if not product:
                return None  # This will trigger the not found response
            return product
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            result = func(*args, **kwargs)
            
            # If result is None, return not found error
            if result is None:
                return error_response_class(
                    message=not_found_message,
                    errors=[not_found_message],
                    line=0,
                    file=func.__module__.split('.')[-1] + '.py',
                    status_code=404,
                    timestamp=datetime.now()
                )
            
            return result
        return wrapper
    return decorator


def _get_session_from_args(*args, **kwargs) -> Optional[Session]:
    """
    Helper function to extract SQLModel Session from function arguments.
    Looks in both positional and keyword arguments.
    """
    # Check keyword arguments first
    session = kwargs.get('session')
    if session and isinstance(session, Session):
        return session
    
    # Check positional arguments
    for arg in args:
        if isinstance(arg, Session):
            return arg
    
    return None