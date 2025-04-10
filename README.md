# Math Operations AI Agent

A Python-based AI agent using LangGraph and Ollama that provides mathematical operations through a REST API. The agent uses a local LLM instance to understand queries and execute math tools.

## Project Overview

This project implements an AI agent that:

- Uses Ollama for local LLM capabilities
- Provides three mathematical tools:
  - Multiply two integers
  - Add two integers
  - Subtract one integer from another
- Exposes a REST API for interacting with the agent
- Uses a direct conversation handling approach for reliable results

### Architecture

The agent consists of several key components:

1. **Tools Module**: Defines the available mathematical operations
2. **Agent Module**: Handles conversation management and LLM interactions
3. **FastAPI Server**: Exposes the agent capabilities as a REST API

## Installation

### Prerequisites

- Python 3.9+
- [Ollama](https://ollama.ai) installed locally with the `llama2` model

### Setup

1. Get the code:
   ```bash
   # Clone or download the project files
   cd langgraph_agent
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Ensure Ollama is running with the llama2 model:
   ```bash
   ollama pull llama2
   ```

## Running the Agent

Start the server with:

```bash
python main.py
```

The server will be available at `http://0.0.0.0:8000`.

## Usage

### Querying the Agent

You can interact with the agent using HTTP requests:

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"query": "Can you help me multiply 23 and 45?"}' \
  http://localhost:8000/agent
```

Example response:
```json
{
  "messages": [
    {
      "type": "human",
      "content": "Can you help me multiply 23 and 45?"
    },
    {
      "type": "ai",
      "content": "I'll help you multiply 23 and 45. Let me break this down."
    },
    {
      "type": "tool",
      "content": "{'result': 1035, 'explanation': 'The product of 23 and 45 is 1035'}",
      "name": "multiply_numbers"
    },
    {
      "type": "system",
      "content": "SYSTEM: Now that you have the calculation result, please provide your FINAL ANSWER."
    },
    {
      "type": "ai",
      "content": "Based on my calculations, I can now answer the question.\n\nFinal answer: The result of multiplying 23 and 45 is 1035. I used the multiply_numbers tool to calculate this product directly."
    }
  ],
  "answer": "Based on my calculations, I can now answer the question.\n\nFinal answer: The result of multiplying 23 and 45 is 1035. I used the multiply_numbers tool to calculate this product directly."
}
```

### Additional Query Examples

**Addition Example:**
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"query": "What is 128 plus 457?"}' \
  http://localhost:8000/agent
```

**Subtraction Example:**
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"query": "Calculate 500 minus 275"}' \
  http://localhost:8000/agent
```

## Extending the Agent

### Adding New Tools

You can extend the agent by adding new mathematical operations or other tools in the `tools.py` file:

1. Define a new Pydantic model for your tool's inputs:
   ```python
   class PowerInput(BaseModel):
       base: int = Field(description="Base number")
       exponent: int = Field(description="Exponent to raise the base to")
   ```

2. Implement the tool function:
   ```python
   def power_number(args: Dict[str, Any]) -> Dict[str, Any]:
       """
       Raises a number to a power.
       
       Args:
           base (int): Base number
           exponent (int): Exponent
       
       Returns:
           Dict[str, Any]: The result of base^exponent
       """
       base = args.get("base")
       exponent = args.get("exponent")
       result = base ** exponent
       return {
           "result": result, 
           "explanation": f"{base} raised to the power of {exponent} is {result}"
       }
   ```

3. Add your tool to the `TOOLS` dictionary:
   ```python
   TOOLS = {
       # ... existing tools ...
       "power_number": {
           "description": "Raises a number to a power",
           "function": power_number,
           "schema": PowerInput,
       },
   }
   ```

4. Update the system prompt in `agent.py` to include your new tool name in the available tools list.

### Modifying Agent Behavior

To modify how the agent processes conversations:

1. Update the `run_conversation` function in `agent.py` to change conversation flow
2. Modify termination conditions in the conversation loop
3. Adjust the system prompt to guide the LLM's behavior

## API Documentation

### Endpoints

#### GET /

Returns a welcome message to confirm the API is running.

**Response:**
```json
{
  "message": "Welcome to the Math Agent API"
}
```

#### POST /agent

Processes a query and returns the agent's response.

**Request Body:**
```json
{
  "query": "string"  // The user's mathematical question
}
```

**Response:**
```json
{
  "messages": [
    {
      "type": "string",  // Message type (human, ai, tool, system)
      "content": "string",  // Message content
      "name": "string"  // Optional, for tool messages
    }
  ],
  "answer": "string"  // The final answer extracted from messages
}
```

## Development Guidelines

When contributing to this project, please follow these guidelines:

1. **Code Organization**:
   - Keep tools in `tools.py`
   - Agent logic stays in `agent.py`
   - API endpoints in `main.py`

2. **Error Handling**:
   - Implement proper error handling in tool functions
   - Provide fallback responses when LLM calls fail
   - Log errors with appropriate detail

3. **Testing**:
   - Test new tools with various inputs
   - Verify agent responses for correctness
   - Check error handling by intentionally breaking inputs

4. **Logging**:
   - Use the established logger for consistency
   - Log important state transitions
   - Include useful context in log messages

5. **Performance**:
   - Keep tool functions efficient
   - Avoid unnecessary LLM calls
   - Implement proper termination conditions

## Troubleshooting

**Common Issues:**

1. **Ollama Connection Errors**:
   - Ensure Ollama is running (`ollama serve`)
   - Check that the llama2 model is pulled (`ollama list`)

2. **Long Response Times**:
   - Reduce the size of the context in complex queries
   - Check system resources if Ollama is running slowly

3. **Tool Execution Errors**:
   - Verify input types match the expected schema
   - Check for proper error handling in tool functions

## License

[MIT License](LICENSE)

