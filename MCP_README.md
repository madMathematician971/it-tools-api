# IT Tools API - MCP Server

This project provides Model Context Protocol (MCP) support for IT Tools API, allowing you to access IT Tools functionality through the Model Context Protocol.

## What is MCP?

The [Model Context Protocol (MCP)](https://modelcontextprotocol.io) lets you build servers that expose data and functionality to LLM applications in a secure, standardized way. Think of it like a web API, but specifically designed for LLM interactions. MCP servers can:

- Expose data through **Resources** (like GET endpoints; they load information into the LLM's context)
- Provide functionality through **Tools** (like POST endpoints; they execute code or produce side effects)
- Define interaction patterns through **Prompts** (reusable templates for LLM interactions)

## Project Structure

The MCP implementation follows a modular structure:

- `mcp_server/__init__.py` - Contains the main MCP app instance used throughout the application
- `mcp_server/tools/` - Contains individual tool implementations
- `mcp_server.py` - Entry point for running the MCP server

## Getting Started

### Installation

Make sure you have the required dependencies:

```bash
# If you're using uv (recommended)
uv add "mcp[cli]"

# If you're using pip
pip install "mcp[cli]"
```

### Running the MCP Server

You can run the MCP server using `uv`:

```bash
# Start the MCP server
uv run mcp_tools_server.py

```

## Available Tools

The MCP server provides the following tools:

### Base Converter

Convert numbers between different numerical bases (2-36).

**Tool Name:** `base_convert`

**Parameters:**
- `number_string`: The number to convert (as a string)
- `input_base`: The base of the input number (2-36)
- `output_base`: The target base for conversion (2-36)

**Example:**
```python
result = await session.call_tool("base_convert", {
    "number_string": "1010", 
    "input_base": 2, 
    "output_base": 10
})
# result: {"result_string": "10", "input_number_string": "1010", "input_base": 2, "output_base": 10}
```

### Hash Calculator

Calculate various hash digests (MD5, SHA1, SHA256, SHA512) for the input text.

**Tool Name:** `calculate_hash`

**Parameters:**
- `text`: The text to hash

**Example:**
```python
result = await session.call_tool("calculate_hash", {
    "text": "Hello, world!"
})
# result: {"md5": "65a8...", "sha1": "2aae...", "sha256": "315f...", "sha512": "c1c9..."}
```

### HMAC Calculator

Calculate HMAC digest for input text using a secret key and hash algorithm.

**Tool Name:** `calculate_hmac`

**Parameters:**
- `text`: The text to calculate HMAC for
- `key`: The secret key
- `algorithm`: Hash algorithm (md5, sha1, sha256, sha512)

**Example:**
```python
result = await session.call_tool("calculate_hmac", {
    "text": "Hello, world!", 
    "key": "secret-key", 
    "algorithm": "sha256"
})
# result: {"hmac_hex": "a31...", "algorithm": "sha256"}
```

### UUID Generator

Generate a UUID of the specified version.

**Tool Name:** `generate_uuid`

**Parameters:**
- `version`: UUID version (1, 3, 4, or 5)
- `namespace`: Namespace UUID (only for version 3 or 5)
- `name`: Name within namespace (only for version 3 or 5)

**Example:**
```python
result = await session.call_tool("generate_uuid", {
    "version": 4
})
# result: {"uuid": "c420...", "version": 4, "variant": "RFC 4122", "is_nil": false, "hex": "c420...", ...}
```

### Math Expression Evaluator

Safely evaluate mathematical expressions.

**Tool Name:** `evaluate_math`

**Parameters:**
- `expression`: The math expression to evaluate

**Example:**
```python
result = await session.call_tool("evaluate_math", {
    "expression": "2 * (3 + 4) / sin(0.5)"
})
# result: {"result": 29.3..., "error": null}
```

### JSON Formatter

Format JSON string with proper indentation and optional key sorting.

**Tool Name:** `format_json`

**Parameters:**
- `json_string`: The JSON string to format
- `indent`: Number of spaces for indentation (default: 4)
- `sort_keys`: Whether to sort keys alphabetically (default: false)

**Example:**
```python
result = await session.call_tool("format_json", {
    "json_string": '{"name":"John","age":30}',
    "indent": 4
})
# result: {"result_string": "{\n    \"name\": \"John\",\n    \"age\": 30\n}", "error": null}
```

### JSON Minifier

Minify a JSON string (remove unnecessary whitespace).

**Tool Name:** `minify_json`

**Parameters:**
- `json_string`: The JSON string to minify

**Example:**
```python
result = await session.call_tool("minify_json", {
    "json_string": '{\n    "name": "John",\n    "age": 30\n}'
})
# result: {"result_string": "{\"name\":\"John\",\"age\":30}", "error": null}
```

### JSON Diff

Compare two JSON objects and return their differences.

**Tool Name:** `json_diff`

**Parameters:**
- `json1`: First JSON string
- `json2`: Second JSON string
- `ignore_order`: Whether to ignore array order (default: false)
- `output_format`: Output format (delta or simple) (default: "delta")

**Example:**
```python
result = await session.call_tool("json_diff", {
    "json1": '{"name":"John","age":30}',
    "json2": '{"name":"John","age":31,"city":"New York"}'
})
# result: {"diff": "...", "format_used": "delta", "error": null}
```

### List Converter

Converts list items from one text format to another.

**Tool Name:** `convert_list`

**Parameters:**
- `input_text`: The list text to convert
- `input_format`: Format of the input list (comma, newline, space, semicolon, bullet_asterisk, bullet_hyphen, numbered_dot, numbered_paren)
- `output_format`: Desired format for the output list
- `ignore_empty`: Ignore empty lines or items during conversion (default: true)
- `trim_items`: Trim whitespace from each list item (default: true)

**Example:**
```python
result = await session.call_tool("convert_list", {
    "input_text": "item1,item2,item3",
    "input_format": "comma",
    "output_format": "bullet_hyphen"
})
# result: {"result": "- item1\n- item2\n- item3", "error": null}
```

### Phone Number Parser

Parse, validate, and format a phone number using the phonenumbers library.

**Tool Name:** `parse_phone_number`

**Parameters:**
- `phone_number_string`: The phone number to parse
- `default_country`: Optional default country code (e.g., US, GB)

**Example:**
```python
result = await session.call_tool("parse_phone_number", {
    "phone_number_string": "+1 (555) 123-4567"
})
# result: {"is_valid": true, "country_code": 1, "national_number": "5551234567", "e164_format": "+15551234567", ...}
```

### Roman Numeral Converter (Encoding)

Convert an integer to its Roman numeral representation.

**Tool Name:** `encode_to_roman`

**Parameters:**
- `number`: Integer to convert to Roman numerals (1-3999)

**Example:**
```python
result = await session.call_tool("encode_to_roman", {
    "number": 42
})
# result: {"input_value": 42, "result": "XLII", "error": null}
```

### Roman Numeral Converter (Decoding)

Convert a Roman numeral string to its integer representation.

**Tool Name:** `decode_from_roman`

**Parameters:**
- `roman_numeral`: Roman numeral string to convert to integer

**Example:**
```python
result = await session.call_tool("decode_from_roman", {
    "roman_numeral": "MMXXIV"
})
# result: {"input_value": "MMXXIV", "result": 2024, "error": null}
```

### Base64 Encoder

Encode a string to Base64.

**Tool Name:** `base64_encode_string`

**Parameters:**
- `input_string`: The string to encode.

**Example:**
```python
result = await session.call_tool("base64_encode_string", {
    "input_string": "Hello, world!"
})
# result: {"result_string": "SGVsbG8sIHdvcmxkIQ==", "error": null}
```

### Base64 Decoder

Decode a Base64 string.

**Tool Name:** `base64_decode_string`

**Parameters:**
- `input_string`: The Base64 string to decode.

**Example:**
```python
result = await session.call_tool("base64_decode_string", {
    "input_string": "SGVsbG8sIHdvcmxkIQ=="
})
# result: {"result_string": "Hello, world!", "error": null}
```

### IPv4 Subnet Calculator

Calculate IPv4 subnet details given an IP address and CIDR prefix or netmask.

**Tool Name:** `calculate_ipv4_subnet`

**Parameters:**
- `ip_cidr`: The IP address and CIDR/mask (e.g., "192.168.1.50/24")

**Example:**
```python
result = await session.call_tool("calculate_ipv4_subnet", {
    "ip_cidr": "192.168.1.50/24"
})
# result: {"network_address": "192.168.1.0", "broadcast_address": "192.168.1.255", "netmask": "255.255.255.0", ...}
```

## Available Resources

### Base Converter Resource

Resource URI: `base://convert/{number}/{from_base}/{to_base}`

**Example:**
```python
content, mime_type = await session.read_resource("base://convert/1010/2/10")
# content: "Converted 1010 from base 2 to base 10: 10"
```

### IT Tools Info

Resource URI: `ittools://info`

Returns general information about the IT Tools API MCP server.

## Available Prompts

### Base Conversion Help

Prompt Name: `base_conversion_help`

Creates a prompt to explain base conversion concepts.

### Cryptography Help

Prompt Name: `cryptography_help`

Creates a prompt to explain cryptographic functions and concepts.

### Adding New Tools

To add more tools to the MCP server, create a new module in the `mcp_server/tools/` directory and define your tool using the global MCP app instance:

```python
from mcp_server import mcp_app

@mcp_app.tool()
def my_new_tool(param1: str, param2: int) -> dict[str, Any]:
    """
    Description of what the tool does.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        A dictionary containing the tool's output
    """
    # Tool implementation
    result = do_something(param1, param2)
    return {"result": result, "error": None}
```

## Running with Docker and Cursor

You can run this MCP server as a Docker container and integrate it with Cursor.

1. **Build the Docker Image:**

   Navigate to the project root directory in your terminal and build the `fastmcp` target from the Dockerfile:

   ```bash
   docker build -t it-tools-mcp:latest --target fastmcp .
   ```
   (Replace `it-tools-mcp:latest` with your desired image name and tag if needed.)

2. **Configure Cursor (`mcp.json`):**

   Open or create your Cursor MCP configuration file (usually at `~/.cursor/mcp.json`). Add an entry similar to this, replacing `it-tools-mcp:latest` if you used a different tag:

   ```json
   {
     "mcpServers": {
       "mcp-it-tools-local": { 
         "command": "docker",
         "args": [
           "run",
           "-i",      // Keep STDIN open even if not attached
           "--rm",    // Automatically remove the container when it exits
           "--init",  // Use an init process as PID 1 to handle signals and reap zombie processes
           "it-tools-mcp:latest" // Use the image built in step 1
         ]
       }
       // ... other server configurations ...
     }
   }
   ```
   - The key `"mcp-it-tools-local"` is the name you'll use to refer to this server in Cursor.
   - `"command": "docker"` tells Cursor to use Docker.
   - The `args` specify how to run the container: `-i` for interactive mode (necessary for MCP's stdio transport) and `--rm` for cleanup.

3. **Restart Cursor:**

   Restart Cursor to apply the changes to `mcp.json`.

4. **Use in Cursor:**

   You should now be able to access the tools provided by this MCP server from within Cursor by referencing the server name (e.g., `@mcp-it-tools-local`).

## License

This project is licensed under the GPL-3.0 license - see the LICENSE file for details. 