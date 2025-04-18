# Tool Unit Tests

This directory contains unit tests for the MCP tool functions, focusing on direct testing of the tool functionality without going through the API routers.

## Purpose

These tests serve several important purposes:

1. **Direct Tool Testing**: Test tool functions directly, without overhead from API routes
2. **Isolated Testing**: Verify that tools work correctly in isolation from the rest of the system
3. **Function Coverage**: Ensure all edge cases and error conditions are tested at the function level
4. **Documentation**: Provide examples of expected inputs and outputs for each tool

## Running the Tests

You can run the tool tests using pytest:

```bash
# Run all tool tests
python -m pytest tests/mcp/tools

# Run tests for a specific tool
python -m pytest tests/mcp/tools/test_base_converter.py
python -m pytest tests/mcp/tools/test_hash_calculator.py
python -m pytest tests/mcp/tools/test_hmac_calculator.py

# Run with verbose output
python -m pytest tests/mcp/tools -v

# Run with coverage report
python -m pytest tests/mcp/tools --cov=mcp_server.tools
```

## Test Structure

Each tool has its own test file with the following sections:

1. **Successful Cases**: Tests with valid inputs that should produce expected outputs
2. **Error Cases**: Tests with invalid inputs that should raise appropriate errors
3. **Edge Cases**: Tests with boundary conditions (empty strings, Unicode characters, etc.)
4. **Known Values**: Tests with pre-calculated expected outputs for specific inputs

## Contributing New Tests

When adding a new tool, please create corresponding tests that follow this pattern:

1. Create a new test file named `test_[tool_name].py`
2. Import the tool function(s) from the appropriate module
3. Test all parameters, including defaults and edge cases
4. Use `pytest.mark.parametrize` for testing multiple input/output combinations
5. Test error conditions with `pytest.raises`
6. Include docstrings for each test function explaining its purpose 