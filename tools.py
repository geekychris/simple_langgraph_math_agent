# Copyright (c) 2025 Chris Collins chris@hitorro.com
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from typing import Dict, Any, Tuple
from pydantic import BaseModel, Field

class MultiplyInput(BaseModel):
    a: int = Field(description="First integer to multiply")
    b: int = Field(description="Second integer to multiply")

class AddInput(BaseModel):
    a: int = Field(description="First integer to add")
    b: int = Field(description="Second integer to add")

class SubtractInput(BaseModel):
    a: int = Field(description="Integer to subtract from")
    b: int = Field(description="Integer to subtract")

def multiply_numbers(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Multiplies two integers together.
    
    Args:
        a (int): First integer
        b (int): Second integer
    
    Returns:
        Dict[str, Any]: The product of the two integers
    """
    a = args.get("a")
    b = args.get("b")
    result = a * b
    return {"result": result, "explanation": f"The product of {a} and {b} is {result}"}

def add_numbers(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Adds two integers together.
    
    Args:
        a (int): First integer
        b (int): Second integer
    
    Returns:
        Dict[str, Any]: The sum of the two integers
    """
    a = args.get("a")
    b = args.get("b")
    result = a + b
    return {"result": result, "explanation": f"The sum of {a} and {b} is {result}"}

def subtract_numbers(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Subtracts one integer from another.
    
    Args:
        a (int): Integer to subtract from
        b (int): Integer to subtract
    
    Returns:
        Dict[str, Any]: The result of subtracting b from a
    """
    a = args.get("a")
    b = args.get("b")
    result = a - b
    return {"result": result, "explanation": f"The result of {a} - {b} is {result}"}

# Dictionary of available tools
TOOLS = {
    "multiply_numbers": {
        "description": "Multiplies two integers together",
        "function": multiply_numbers,
        "schema": MultiplyInput,
    },
    "add_numbers": {
        "description": "Adds two integers together",
        "function": add_numbers,
        "schema": AddInput,
    },
    "subtract_numbers": {
        "description": "Subtracts one integer from another",
        "function": subtract_numbers,
        "schema": SubtractInput,
    },
}

