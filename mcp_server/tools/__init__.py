"""
MCP tools for IT Tools API.
"""

from mcp_server.tools.base64_converter import base64_decode_string, base64_encode_string
from mcp_server.tools.base_converter import base_convert
from mcp_server.tools.basic_auth_generator import generate_basic_auth_header
from mcp_server.tools.bip39_generator import generate_bip39_mnemonic
from mcp_server.tools.case_converter import convert_case
from mcp_server.tools.chmod_calculator import calculate_numeric_chmod, calculate_symbolic_chmod
from mcp_server.tools.color_converter import convert_color
from mcp_server.tools.cron_parser import describe_cron, validate_cron
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
