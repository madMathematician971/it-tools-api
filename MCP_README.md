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

### Data Format Converter

Convert data between JSON, YAML, TOML, and XML formats.

**Tool Name:** `convert_data`

**Parameters:**
- `input_string`: The data string to convert.
- `input_type`: The format of the input string ('json', 'yaml', 'toml', 'xml').
- `output_type`: The desired output format ('json', 'yaml', 'toml', 'xml').

**Example:**
```python
result = await session.call_tool("convert_data", {
    "input_string": '{"name":"Test", "value":123}',
    "input_type": "json",
    "output_type": "yaml"
})
# result: {"output_string": "name: Test\nvalue: 123\n", "error": null}
```

### Datetime Converter

Converts a date/time string from one format to another, automatically detecting the input format if possible. Handles various formats and timezones.

**API Endpoint:** `/api/datetime/convert`
**MCP Tool Function:** `mcp_server.tools.datetime_parser.parse_datetime`

**Parameters:**
- `input_value`: The date/time string to parse (e.g., "2023-10-26T10:00:00Z", "October 26, 2023 10:00 AM UTC", "1666788000").
- `input_format`: Optional Python `strptime` format string to specify the exact input format. If omitted, the tool attempts auto-detection.
- `output_format`: Python `strftime` format string for the desired output (e.g., `"%Y-%m-%d %H:%M:%S %Z"`).

**Example:**
```python
result = await session.call_tool("parse_datetime", {
    "input_value": "2023-10-26T10:00:00Z",
    "output_format": "%A, %B %d, %Y %I:%M:%S %p %Z"
})
# result: {
#   "result_string": "Thursday, October 26, 2023 10:00:00 AM UTC",
#   "input_value": "2023-10-26T10:00:00Z",
#   "input_format_used": "%Y-%m-%dT%H:%M:%SZ", # Detected format
#   "output_format": "%A, %B %d, %Y %I:%M:%S %p %Z",
#   "parsed_datetime": "2023-10-26T10:00:00+00:00",
#   "timezone_name": "UTC",
#   "error": null,
#   ... (other parsed components)
# }
```

### Docker Run to Compose Converter

Converts a `docker run` command string into a basic `docker-compose.yml` YAML structure.

**API Endpoint:** `/api/docker/run-to-compose`
**MCP Tool Function:** `mcp_server.tools.docker_converter.convert_run_to_compose`

**Parameters:**
- `docker_run_command`: The full `docker run ...` command string.

**Example:**
```python
result = await session.call_tool("convert_run_to_compose", {
    "docker_run_command": "docker run -d --name my-app -p 8080:80 my-image:latest"
})
# result: {
#   "docker_compose_yaml": "services:\n  my-app:\n    image: my-image:latest\n    ports:\n    - 8080:80\n    container_name: my-app\n",
#   "error": null
# }
```

### Email Normalizer

Validates and normalizes an email address based on common provider rules (Gmail/Google, Outlook/Hotmail/Live), removing dots and sub-addressing (+) where applicable.

**API Endpoint:** `/api/email/normalize`
**MCP Tool Function:** `mcp_server.tools.email_processor.normalize_email`

**Parameters:**
- `email_address`: The email address string to validate and normalize.

**Example:**
```python
result = await session.call_tool("normalize_email", {
    "email_address": "Test.User+alias@gmail.com"
})
# result: {
#   "normalized_email": "testuser@gmail.com",
#   "original_email": "Test.User+alias@gmail.com",
#   "error": null
# }

result = await session.call_tool("normalize_email", {
    "email_address": "invalid-email"
})
# result: {
#   "normalized_email": null,
#   "original_email": "invalid-email",
#   "error": "Invalid email format."
# }
```

### AES Encryptor (AES-256-CBC)

Encrypt text using AES-256-CBC. It uses PBKDF2-HMAC-SHA256 to derive a key from the password and includes a random salt and IV in the output ciphertext.

**API Endpoint:** `/api/crypto/encrypt`
**MCP Tool Function:** `mcp_server.tools.encryption_processor.encrypt_text`

**Parameters:**
- `text`: The plaintext string to encrypt.
- `password`: The password for key derivation.
- `algorithm`: Must be "aes-256-cbc".

**Example:**
```python
result = await session.call_tool("encrypt_text", {
    "text": "Secret data",
    "password": "supersecure",
    "algorithm": "aes-256-cbc"
})
# result: {
#   "ciphertext": "Base64StringContainingSaltAndIVAndCiphertext==",
#   "error": null
# }
```

### AES Decryptor (AES-256-CBC)

Decrypt text that was encrypted using the corresponding AES-256-CBC encryption tool. It extracts the salt and IV from the ciphertext and re-derives the key using PBKDF2.

**API Endpoint:** `/api/crypto/decrypt`
**MCP Tool Function:** `mcp_server.tools.encryption_processor.decrypt_text`

**Parameters:**
- `ciphertext`: The Base64 encoded string containing salt, IV, and encrypted data.
- `password`: The password used during encryption.
- `algorithm`: Must be "aes-256-cbc".

**Example:**
```python
# Assuming 'ciphertext_from_encrypt' is the result from the encrypt_text tool
result = await session.call_tool("decrypt_text", {
    "ciphertext": ciphertext_from_encrypt,
    "password": "supersecure",
    "algorithm": "aes-256-cbc"
})
# result: {
#   "plaintext": "Secret data",
#   "error": null
# }

# Example with wrong password
result = await session.call_tool("decrypt_text", {
    "ciphertext": ciphertext_from_encrypt,
    "password": "wrongpassword",
    "algorithm": "aes-256-cbc"
})
# result: {
#   "plaintext": null,
#   "error": "Decryption failed. Likely incorrect password or corrupt/invalid data."
# }
```

### ETA Calculator

Calculates the end datetime by adding a duration (in seconds) to a start datetime provided in ISO 8601 format. Assumes UTC if no timezone is provided in the start time.

**API Endpoint:** `/api/eta/calculate`
**MCP Tool Function:** `mcp_server.tools.eta_calculator.calculate_eta`

**Parameters:**
- `start_time_iso`: The starting datetime in ISO 8601 format (e.g., '2023-10-27T10:00:00Z').
- `duration_seconds`: The duration in seconds to add (must be non-negative).

**Example:**
```python
result = await session.call_tool("calculate_eta", {
    "start_time_iso": "2024-01-01T12:00:00+01:00",
    "duration_seconds": 3660
})
# result: {
#   "start_time": "2024-01-01T12:00:00+01:00",
#   "duration_seconds": 3660,
#   "end_time": "2024-01-01T13:01:00+01:00",
#   "error": null
# }
```

### IPv4 Address Converter

Converts an IPv4 address between dotted decimal, integer, hexadecimal, and binary formats. It can auto-detect the input format or use an optional hint.

**API Endpoint:** `/api/ipv4-converter/`
**MCP Tool Function:** `mcp_server.tools.ipv4_converter.convert_ipv4`

**Parameters:**
- `ip_address`: The IP address string (e.g., "192.168.1.1", "3232235777", "0xC0A80101").
- `format_hint`: Optional hint (`dotted`, `decimal`, `hex`, `binary`) to specify input format.

**Example (Auto-detect):**
```python
result = await session.call_tool("convert_ipv4", {
    "ip_address": "192.168.1.1"
})
# result: {
#   "original": "192.168.1.1",
#   "dotted_decimal": "192.168.1.1",
#   "decimal": 3232235777,
#   "hexadecimal": "0xC0A80101",
#   "binary": "11000000101010000000000100000001",
#   "error": null
# }
```

**Example (With Hint):**
```python
result = await session.call_tool("convert_ipv4", {
    "ip_address": "C0A80101",
    "format_hint": "hex"
})
# result: {
#   "original": "C0A80101",
#   "dotted_decimal": "192.168.1.1",
#   "decimal": 3232235777,
#   "hexadecimal": "0xC0A80101",
#   "binary": "11000000101010000000000100000001",
#   "error": null
# }
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

### Basic Auth Header Generator

Generate a Basic Authentication HTTP header string.

**Tool Name:** `generate_basic_auth_header`

**Parameters:**
- `username`: The username for authentication.
- `password`: The password for authentication.

**Example:**
```python
result = await session.call_tool("generate_basic_auth_header", {
    "username": "testuser",
    "password": "p@ssword"
})
# result: {"username": "testuser", "password": "p@ssword", "encoded": "dGVzdHVzZXI6cEBzc3dvcmQ=", "header": "Basic dGVzdHVzZXI6cEBzc3dvcmQ=", "error": null}
```

### BIP39 Mnemonic Generator

Generate a BIP39 mnemonic seed phrase for cryptocurrency wallets.

**Tool Name:** `generate_bip39_mnemonic`

**Parameters:**
- `word_count`: Number of words (12, 15, 18, 21, 24).
- `language`: Language code (e.g., 'en', 'es', 'jp'). Defaults to 'en'.

**Example:**
```python
result = await session.call_tool("generate_bip39_mnemonic", {
    "word_count": 12,
    "language": "en"
})
# result: {"mnemonic": "word1 word2 ... word12", "word_count": 12, "language": "english", "error": null}
```

### Case Converter

Convert a string to various case formats (camel, snake, pascal, etc.).

**Tool Name:** `convert_case`

**Parameters:**
- `input_string`: The string to convert.
- `target_case`: Target case format (e.g., 'camel', 'snake', 'pascal', 'constant', 'kebab', 'capital', 'lower', 'upper').

**Example:**
```python
result = await session.call_tool("convert_case", {
    "input_string": "hello world",
    "target_case": "pascal"
})
# result: {"result": "HelloWorld", "error": null}
```

### Chmod Calculator (Numeric from Symbolic)

Calculate the numeric (octal) chmod value from individual permission settings.

**Tool Name:** `calculate_numeric_chmod`

**Parameters:**
- `owner_read`: Owner read permission (bool).
- `owner_write`: Owner write permission (bool).
- `owner_execute`: Owner execute permission (bool).
- `group_read`: Group read permission (bool).
- `group_write`: Group write permission (bool).
- `group_execute`: Group execute permission (bool).
- `others_read`: Others read permission (bool).
- `others_write`: Others write permission (bool).
- `others_execute`: Others execute permission (bool).

**Example:**
```python
result = await session.call_tool("calculate_numeric_chmod", {
    "owner_read": True, "owner_write": True, "owner_execute": False,
    "group_read": True, "group_write": False, "group_execute": True,
    "others_read": True, "others_write": False, "others_execute": False
})
# result: {"numeric_chmod": "654", "error": null}
```

### Chmod Calculator (Symbolic from Numeric)

Convert a numeric chmod value (e.g., "755", "644") to its symbolic representation.

**Tool Name:** `calculate_symbolic_chmod`

**Parameters:**
- `numeric_chmod_string`: The numeric value as a string (e.g., "755", "0644", "5").

**Example:**
```python
result = await session.call_tool("calculate_symbolic_chmod", {
    "numeric_chmod_string": "755"
})
# result: {"symbolic_chmod": "rwxr-xr-x", "error": null}
```

### Color Converter

Convert colors between various formats (hex, rgb, hsl, web names).

**Tool Name:** `convert_color`

**Parameters:**
- `input_color`: Color string (e.g., "#ff0000", "red", "hsl(0, 100%, 50%)"). Works best with hex or web names.
- `target_format`: Desired output format (e.g., "hex", "rgb", "hsl", "web", "luminance").

**Example:**
```python
result = await session.call_tool("convert_color", {
    "input_color": "#336699",
    "target_format": "rgb"
})
# result: {"result": "rgb(51, 102, 153)", "input_color": "#336699", "target_format": "rgb", "parsed_hex": "#336699", "parsed_rgb": "rgb(51, 102, 153)", "parsed_hsl": "hsl(210, 50%, 40%)", "error": null}
```

### Cron Descriptor

Get a human-readable description of a 5-field cron string.
Validates both 5 and 6-field strings but only describes the 5-field standard.

**Tool Name:** `describe_cron`

**Parameters:**
- `cron_string`: The cron expression (e.g., "*/5 * * * *", "0 9 * * MON-FRI").

**Example:**
```python
result = await session.call_tool("describe_cron", {
    "cron_string": "0 9 * * 1-5"
})
# result: {"description": "At 09:00 AM, Monday through Friday", "error": null}

result = await session.call_tool("describe_cron", {
    "cron_string": "* * * * * *" # 6-field input
})
# result: {"description": "Valid 6-field cron string (includes seconds). Description only provided for 5-field standard.", "error": null}
```

### Cron Validator

Validate a cron string (5 or 6 fields) and get the next 5 predicted run times.

**Tool Name:** `validate_cron`

**Parameters:**
- `cron_string`: The cron expression (e.g., "0 0 * * 0", "*/10 * * * * *").

**Example:**
```python
result = await session.call_tool("validate_cron", {
    "cron_string": "0 0 * * SUN"
})
# result: {"is_valid": true, "next_runs": ["2024-...\T00:00:00+00:00", ...], "error": null}

result = await session.call_tool("validate_cron", {
    "cron_string": "invalid"
})
# result: {"is_valid": false, "next_runs": null, "error": "Invalid cron string format."}
```

### IPv4 Range Expander

Expands an IPv4 range provided in CIDR or hyphenated format into a list of individual IP addresses. The result may be truncated if the range exceeds a predefined limit (65536).

**Tool Name:** `expand_ipv4_range`

**Parameters:**
- `ip_range`: The IPv4 range string (e.g., "192.168.1.0/24", "10.0.0.1-10.0.0.10").

**Example:**
```python
result = await session.call_tool("expand_ipv4_range", {
    "ip_range": "192.168.1.254/30"
})
# result: {"count": 4, "addresses": ["192.168.1.252", "192.168.1.253", "192.168.1.254", "192.168.1.255"], "truncated": false, "error": null}

result = await session.call_tool("expand_ipv4_range", {
    "ip_range": "10.0.0.1-10.0.0.3"
})
# result: {"count": 3, "addresses": ["10.0.0.1", "10.0.0.2", "10.0.0.3"], "truncated": false, "error": null}

# Example with truncation (if MAX_ADDRESSES_TO_RETURN is 65536)
result = await session.call_tool("expand_ipv4_range", {
    "ip_range": "10.0.0.0/15" # > 65536 addresses
})
# result: {"count": 131072, "addresses": ["10.0.0.0", ..., "10.0.255.255"], "truncated": true, "error": null}
```

### HTML Entity Encoder

Encode special characters (like <, >, &, ", ') in text into their corresponding HTML entities.

**API Endpoint:** `/api/html-entities/encode`
**MCP Tool Function:** `mcp_server.tools.html_entities_processor.encode_html_entities`

**Parameters:**
- `text`: The input string to encode.

**Example:**
```python
result = await session.call_tool("encode_html_entities", {
    "text": "<p class=\"my-class\">It's > 5 & < 10</p>"
})
# result: {
#   "result": "&lt;p class=&quot;my-class&quot;&gt;It&#x27;s &gt; 5 &amp; &lt; 10&lt;/p&gt;",
#   "error": null
# }
```

### HTML Entity Decoder

Decode HTML entities (like &lt;, &gt;, &amp;, &quot;, &#x27;) in text back into their original characters.

**API Endpoint:** `/api/html-entities/decode`
**MCP Tool Function:** `mcp_server.tools.html_entities_processor.decode_html_entities`

**Parameters:**
- `text`: The input string containing HTML entities.

**Example:**
```python
result = await session.call_tool("decode_html_entities", {
    "text": "&lt;p class=&quot;my-class&quot;&gt;It&#x27;s &gt; 5 &amp; &lt; 10&lt;/p&gt;"
})
# result: {
#   "result": "<p class=\"my-class\">It's > 5 & < 10</p>",
#   "error": null
# }
```

### IBAN Validator

Validates an IBAN string using the `schwifty` library and parses its components if valid. Handles checksum validation, length checks, country code validation, and BBAN structure.

**API Endpoint:** `/api/iban/validate`
**MCP Tool Function:** `mcp_server.tools.iban_processor.validate_iban`

**Parameters:**
- `iban_string`: The IBAN string to validate.

**Example (Valid):**
```python
result = await session.call_tool("validate_iban", {
    "iban_string": "DE89 3704 0044 0532 0130 00"
})
# result: {
#   "is_valid": true,
#   "iban_string_formatted": "DE89 3704 0044 0532 0130 00",
#   "country_code": "DE",
#   "check_digits": "89",
#   "bban": "370400440532013000",
#   "error": null
# }
```

**Example (Invalid):**
```python
result = await session.call_tool("validate_iban", {
    "iban_string": "DE89 3704 0044 0532 0130 01"
})
# result: {
#   "is_valid": false,
#   "iban_string_formatted": null,
#   "country_code": null,
#   "check_digits": null,
#   "bban": null,
#   "error": "Invalid checksum digits"
# }
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