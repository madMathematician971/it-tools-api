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
from mcp_server.tools.data_converter import convert_data
from mcp_server.tools.datetime_parser import parse_datetime
from mcp_server.tools.docker_converter import convert_run_to_compose
from mcp_server.tools.email_processor import normalize_email
from mcp_server.tools.encryption_processor import decrypt_text, encrypt_text
from mcp_server.tools.eta_calculator import calculate_eta
from mcp_server.tools.hash_calculator import calculate_hash
from mcp_server.tools.hmac_calculator import calculate_hmac
from mcp_server.tools.html_entities_processor import decode_html_entities, encode_html_entities
from mcp_server.tools.iban_processor import validate_iban
from mcp_server.tools.ipv4_converter import convert_ipv4
from mcp_server.tools.ipv4_range_expander import expand_ipv4_range
from mcp_server.tools.ipv4_subnet_calculator import calculate_ipv4_subnet
from mcp_server.tools.ipv6_ula_generator import generate_ipv6_ula
from mcp_server.tools.json_csv_converter import csv_to_json, json_to_csv
from mcp_server.tools.json_diff import json_diff
from mcp_server.tools.json_formatter import format_json, minify_json
from mcp_server.tools.jwt_processor import parse_jwt
from mcp_server.tools.list_converter import convert_list
from mcp_server.tools.lorem_generator import generate_lorem
from mcp_server.tools.math_evaluator import evaluate_math
from mcp_server.tools.phone_parser import parse_phone_number
from mcp_server.tools.roman_numeral_converter import decode_from_roman, encode_to_roman
from mcp_server.tools.uuid_generator import generate_uuid
