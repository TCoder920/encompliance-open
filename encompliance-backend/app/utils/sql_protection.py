import logging
import re
import functools
import inspect
from typing import Callable, Any, Dict, List, Optional, Tuple, Union
import sqlalchemy
from sqlalchemy.sql.expression import text

logger = logging.getLogger(__name__)

class SQLInjectionError(Exception):
    """Exception raised when potential SQL injection is detected."""
    pass

def detect_sql_injection(query: str) -> bool:
    """
    Detect potential SQL injection patterns in a string.
    
    Args:
        query: The string to check for SQL injection patterns
        
    Returns:
        bool: True if SQL injection is detected, False otherwise
    """
    # List of common SQL injection patterns
    sql_injection_patterns = [
        r"(\b|')OR(\b|')",
        r"(\b|')AND(\b|')",
        r"--",
        r";",
        r"'.*'",
        r"/\*.*\*/",
        r"xp_cmdshell",
        r"exec\(",
        r"UNION\s+SELECT",
        r"SELECT\s+.*\s+FROM",
        r"INSERT\s+INTO",
        r"UPDATE\s+.*\s+SET",
        r"DELETE\s+FROM",
        r"DROP\s+TABLE",
        r"ALTER\s+TABLE",
        r"WAITFOR\s+DELAY",
        r"1=1",
        r"1\s*=\s*1"
    ]
    
    # Combine patterns into a single regex
    combined_pattern = "|".join(sql_injection_patterns)
    
    # Check if any patterns are found
    if re.search(combined_pattern, query, re.IGNORECASE):
        return True
        
    return False

def sql_injection_protection(func: Callable) -> Callable:
    """
    Decorator to check function arguments for SQL injection patterns.
    
    This decorator should be applied to functions that directly construct
    SQL queries with string parameters.
    
    Args:
        func: The function to decorate
        
    Returns:
        Callable: The decorated function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Get function signature
        sig = inspect.signature(func)
        
        # Map positional and keyword arguments to parameter names
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()
        
        # Check all arguments for SQL injection patterns
        for param_name, param_value in bound_args.arguments.items():
            if isinstance(param_value, str):
                if detect_sql_injection(param_value):
                    logger.warning(f"Potential SQL injection detected in parameter {param_name} of function {func.__name__}")
                    raise SQLInjectionError(f"Invalid input in parameter {param_name}")
        
        # If no SQL injection patterns found, call the original function
        return func(*args, **kwargs)
    
    return wrapper

def use_parameterized_query(query_text: str, params: Dict[str, Any]) -> sqlalchemy.sql.expression.TextClause:
    """
    Create a parameterized SQL query using SQLAlchemy text().
    
    Args:
        query_text: SQL query text with named parameters (e.g., :param_name)
        params: Dictionary of parameter values
        
    Returns:
        sqlalchemy.sql.expression.TextClause: Parameterized query
    """
    # Create SQLAlchemy text object with the query
    sql_text = text(query_text)
    
    # Bind parameters
    for param_name, param_value in params.items():
        sql_text = sql_text.bindparams(sqlalchemy.bindparam(param_name, param_value))
    
    return sql_text

# Usage example:
# @sql_injection_protection
# def get_user_by_username(db_session, username: str):
#     # Safe: Use parameterized query
#     query = use_parameterized_query(
#         "SELECT * FROM users WHERE username = :username",
#         {"username": username}
#     )
#     return db_session.execute(query).fetchone() 