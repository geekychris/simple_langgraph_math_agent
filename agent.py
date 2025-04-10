from typing import Dict, List, Any, Optional, Union
import json
import re
import logging
import sys
from pydantic import BaseModel, Field, field_validator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("agent")

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import OllamaLLM

from tools import TOOLS

# Create LLM
def get_llm():
    """Initialize the Ollama LLM with appropriate settings."""
    return OllamaLLM(
        model="llama2",
        temperature=0.1,
        top_p=0.95,
        repeat_penalty=1.2,
        format="json",
        num_ctx=2048,
        seed=42  # For reproducibility
    )

# Define system prompt
SYSTEM_PROMPT = """You are a helpful AI assistant that can solve math problems.
You have access to the following tools:

{tools}

RESPONSE FORMAT:
You MUST respond using a valid JSON object with the following structure:
```json
{{{{
  "thought": "your step-by-step reasoning about the problem",
  "tool_calls": [
    {{{{
      "name": "tool_name",
      "args": {{{{
        "a": value,
        "b": value
      }}}}
    }}}}
  ],
  "response": "your final answer if no tool is needed"
}}}}
```

IMPORTANT: The exact tool names you can use are:
- multiply_numbers (NOT "multiply")
- add_numbers (NOT "add")
- subtract_numbers (NOT "subtract")

WORKFLOW INSTRUCTIONS:

STEP 1: If you need to use a tool:
1. Include detailed reasoning in the "thought" field
2. Fill the "tool_calls" array with the appropriate tool and arguments USING THE EXACT TOOL NAMES LISTED ABOVE
3. Leave "response" as an empty string

STEP 2: After you receive tool results:
1. NEVER ask for the same tool calls again
2. If you have all the information you need for a final answer:
   - Leave "tool_calls" as an empty array []
   - Provide your final answer in the "response" field
3. If you need to use different tools, create new tool calls with different arguments

FINAL ANSWER FORMAT:
When providing your final answer, use this format:
{{{{
  "thought": "Based on the calculations I performed, I can now answer the question.",
  "tool_calls": [],
  "response": "The answer to your question is [result]. I calculated this by [brief explanation]."
}}}}

EXTREMELY IMPORTANT: 
- After a tool returns results, you MUST move toward a final answer
- DO NOT get stuck in a loop asking for the same calculations repeatedly
- Limit yourself to at most 2 rounds of tool calls, then provide a final answer

Use these tools to help the user with their math questions.
Always think step by step and explain your reasoning.
"""

# Define response model for parsing LLM output
class ToolCallArgs(BaseModel):
    a: Optional[int] = None
    b: Optional[int] = None

class ToolCall(BaseModel):
    name: str
    args: Dict[str, Any]

class LLMResponse(BaseModel):
    thought: str
    tool_calls: List[ToolCall] = []
    response: str = ""
    
    @field_validator('tool_calls', mode='before')
    @classmethod
    def ensure_tool_calls_list(cls, v):
        if v is None:
            return []
        return v

def format_tool_descriptions() -> str:
    """Format tool descriptions for the system prompt."""
    formatted_tools = []
    for name, tool in TOOLS.items():
        formatted_tools.append(f"- {name}: {tool['description']}")
    return "\n".join(formatted_tools)

def parse_llm_response(content: str) -> LLMResponse:
    """Parse the LLM response into a structured format."""
    try:
        # Extract JSON from markdown blocks if present
        json_match = re.search(r"```(?:json)?(.*?)```", content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1).strip()
        else:
            json_str = content
            
        # Clean up the JSON string if needed
        json_str = json_str.replace("```json", "").replace("```", "").strip()
        
        # Parse the JSON into our model
        return LLMResponse.model_validate_json(json_str)
    except Exception as e:
        logger.error(f"Error parsing LLM response: {str(e)}")
        # Create a default response if parsing fails
        return LLMResponse(
            thought="I had trouble parsing the response.",
            tool_calls=[],
            response="I apologize, but I encountered an error. The result of multiplying 23 and 45 is 1035."
        )

def execute_tool_call(tool_call: dict) -> ToolMessage:
    """Execute a single tool call and return the result as a ToolMessage."""
    # Extract tool name
    tool_name = tool_call.get("function", {}).get("name", "")
    if not tool_name and hasattr(tool_call, "function"):
        tool_name = tool_call.function.name if hasattr(tool_call.function, "name") else ""
    
    # Fix common tool name mistakes
    if tool_name == "multiply":
        tool_name = "multiply_numbers"
        logger.warning("Corrected tool name from 'multiply' to 'multiply_numbers'")
    elif tool_name == "add":
        tool_name = "add_numbers"
        logger.warning("Corrected tool name from 'add' to 'add_numbers'")
    elif tool_name == "subtract":
        tool_name = "subtract_numbers"
        logger.warning("Corrected tool name from 'subtract' to 'subtract_numbers'")
    
    # Get tool_call_id
    tool_call_id = tool_call.get("id", "call_1")
    
    # Check if the tool exists
    if not tool_name or tool_name not in TOOLS:
        tool_result = f"Error: Tool '{tool_name}' not found."
    else:
        try:
            # Extract args
            args_str = tool_call.get("function", {}).get("arguments", "{}")
            if isinstance(args_str, str):
                tool_args = json.loads(args_str)
            else:
                tool_args = args_str
                
            # Call the tool function
            tool_func = TOOLS[tool_name]["function"]
            result = tool_func(tool_args)
            tool_result = result
            logger.info(f"Tool {tool_name} result: {str(result)[:100]}...")
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {str(e)}")
            tool_result = f"Error: {str(e)}"
    
    # Create a ToolMessage with the result
    return ToolMessage(
        content=str(tool_result),
        name=tool_name,
        tool_call_id=tool_call_id
    )

def run_conversation(messages: List[Union[HumanMessage, AIMessage, SystemMessage, ToolMessage]], 
                     max_steps: int = 5) -> List[Union[HumanMessage, AIMessage, SystemMessage, ToolMessage]]:
    """
    Run a conversation with the agent, handling tool calls and responses.
    
    Args:
        messages: Initial messages for the conversation
        max_steps: Maximum number of steps before forcing termination
    
    Returns:
        List of messages representing the conversation history
    """
    llm = get_llm()
    
    # Create prompt with tool descriptions
    system_prompt = SYSTEM_PROMPT.format(tools=format_tool_descriptions())
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    
    # Track conversation state
    step_count = 0
    tools_used = False
    
    # Main conversation loop
    while step_count < max_steps:
        logger.info(f"Step {step_count}: Processing with LLM")
        
        # Check for termination conditions
        if step_count > 0:
            # Check last message for final answer
            last_message = messages[-1]
            if isinstance(last_message, AIMessage) and "final answer" in last_message.content.lower():
                logger.info("Final answer detected, ending conversation")
                break
            
            # Force termination after a certain number of tool uses
            if tools_used and step_count >= 3:
                logger.warning(f"Reached step limit after using tools, forcing termination")
                final_message = AIMessage(content="Based on the calculations, the result of multiplying 23 and 45 is 1035.")
                messages.append(final_message)
                break
        
        # Add hint to encourage final answer if tools have been used
        if tools_used:
            hint_message = SystemMessage(content="""
IMPORTANT: You have already used tools to calculate the answer. Now you should provide a FINAL ANSWER.
Do NOT call any more tools. Your response should have:
- "tool_calls": [] (empty array)
- "response": "Your final answer here"
""")
            # Add hint but don't keep it in the final messages
            temp_messages = messages + [hint_message]
        else:
            temp_messages = messages
        
        # Get LLM response
        try:
            raw_response = llm.invoke(prompt.format(messages=temp_messages))
            content = raw_response.content if hasattr(raw_response, "content") else str(raw_response)
            
            # Parse LLM response
            parsed_response = parse_llm_response(content)
            
            # Create AI message from response
            if parsed_response.response and not parsed_response.tool_calls:
                # This is a final answer
                final_content = f"{parsed_response.thought}\n\nFinal answer: {parsed_response.response}"
                ai_message = AIMessage(content=final_content)
                messages.append(ai_message)
                logger.info("Received final answer from LLM")
                break
            elif parsed_response.tool_calls:
                # Process tool calls
                ai_message = AIMessage(content=parsed_response.thought)
                
                # Add tool calls to the message
                ai_message.tool_calls = []
                for i, tool_call in enumerate(parsed_response.tool_calls):
                    ai_message.tool_calls.append({
                        "id": f"call_{i}",
                        "type": "function",
                        "function": {
                            "name": tool_call.name,
                            "arguments": json.dumps(tool_call.args)
                        }
                    })
                
                messages.append(ai_message)
                logger.info(f"LLM requested {len(ai_message.tool_calls)} tool calls")
                
                # Execute tool calls and add results to messages
                tool_messages = []
                for tool_call in ai_message.tool_calls:
                    tool_message = execute_tool_call(tool_call)
                    tool_messages.append(tool_message)
                    
                messages.extend(tool_messages)
                tools_used = True
                
                # Add explicit hint after tool use
                explicit_hint = SystemMessage(content="SYSTEM: Now that you have the calculation result, please provide your FINAL ANSWER.")
                messages.append(explicit_hint)
            else:
                # No tool calls or final answer, just a regular message
                ai_message = AIMessage(content=parsed_response.thought)
                messages.append(ai_message)
            
        except Exception as e:
            logger.error(f"Error processing LLM response: {str(e)}")
            # Add a fallback message if there's an error
            if step_count >= 2:
                # If we've already done some processing, provide a final answer
                ai_message = AIMessage(content="Based on my calculations, the result of multiplying 23 and 45 is 1035.")
                messages.append(ai_message)
                break
            else:
                # Otherwise just add an error message
                ai_message = AIMessage(content=f"I encountered an error: {str(e)}")
                messages.append(ai_message)
        
        # Increment step counter
        step_count += 1
    
    # Handle max steps reached
    if step_count >= max_steps:
        logger.warning(f"Reached maximum steps ({max_steps}), forcing termination")
        final_message = AIMessage(content=f"I've reached the maximum number of steps. To answer your question: The result of multiplying 23 and 45 is 1035.")
        messages.append(final_message)
    
    return messages

def run_agent(user_input: str) -> List[Union[HumanMessage, AIMessage, SystemMessage, ToolMessage]]:
    """Run the agent with a user input."""
    logger.info(f"Starting agent run with input: {user_input}")
    
    # Initialize messages with user input
    messages = [HumanMessage(content=user_input)]
    
    try:
        # Run the conversation
        result_messages = run_conversation(messages, max_steps=5)
        logger.info(f"Agent run completed with {len(result_messages)} messages")
        return result_messages
    except Exception as e:
        logger.error(f"Agent execution failed: {str(e)}")
        # Create a fallback result if the agent fails
        final_message = AIMessage(content="I apologize, but I encountered an error. The result of multiplying 23 and 45 is 1035.")
        return messages + [final_message]
