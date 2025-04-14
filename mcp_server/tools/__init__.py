"""
MCP tools for IT Tools API.
"""

# Import all tools so they can be imported directly from mcp.tools
from mcp_server.tools.base_converter import base_convert
from mcp_server.tools.hash_calculator import calculate_hash
from mcp_server.tools.hmac_calculator import calculate_hmac
from mcp_server.tools.ipv4_subnet_calculator import calculate_ipv4_subnet
from mcp_server.tools.json_diff import json_diff
from mcp_server.tools.json_formatter import format_json, minify_json
from mcp_server.tools.list_converter import convert_list
from mcp_server.tools.math_evaluator import evaluate_math
from mcp_server.tools.phone_parser import parse_phone_number
from mcp_server.tools.roman_numeral_converter import decode_from_roman, encode_to_roman
from mcp_server.tools.uuid_generator import generate_uuid
