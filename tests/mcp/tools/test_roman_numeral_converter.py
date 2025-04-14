"""
Unit tests for the Roman numeral converter tool.
"""

from mcp_server.tools.roman_numeral_converter import decode_from_roman, encode_to_roman

# --- Test Successful Roman Numeral Encoding ---


def test_encode_basic_numerals():
    """Test encoding basic Roman numerals."""
    test_cases = [
        (1, "I"),
        (5, "V"),
        (10, "X"),
        (50, "L"),
        (100, "C"),
        (500, "D"),
        (1000, "M"),
    ]

    for number, expected in test_cases:
        result = encode_to_roman(number=number)
        assert result["input_value"] == number
        assert result["result"] == expected
        assert result["error"] is None


def test_encode_subtractive_combinations():
    """Test encoding Roman numerals with subtractive combinations."""
    test_cases = [
        (4, "IV"),  # 5-1
        (9, "IX"),  # 10-1
        (40, "XL"),  # 50-10
        (90, "XC"),  # 100-10
        (400, "CD"),  # 500-100
        (900, "CM"),  # 1000-100
    ]

    for number, expected in test_cases:
        result = encode_to_roman(number=number)
        assert result["input_value"] == number
        assert result["result"] == expected
        assert result["error"] is None


def test_encode_compound_numerals():
    """Test encoding compound Roman numerals."""
    test_cases = [
        (3, "III"),
        (14, "XIV"),
        (19, "XIX"),
        (24, "XXIV"),
        (42, "XLII"),
        (99, "XCIX"),
        (444, "CDXLIV"),
        (999, "CMXCIX"),
        (2023, "MMXXIII"),
        (3999, "MMMCMXCIX"),  # Maximum supported value
    ]

    for number, expected in test_cases:
        result = encode_to_roman(number=number)
        assert result["input_value"] == number
        assert result["result"] == expected
        assert result["error"] is None


# --- Test Successful Roman Numeral Decoding ---


def test_decode_basic_numerals():
    """Test decoding basic Roman numerals."""
    test_cases = [
        ("I", 1),
        ("V", 5),
        ("X", 10),
        ("L", 50),
        ("C", 100),
        ("D", 500),
        ("M", 1000),
    ]

    for roman, expected in test_cases:
        result = decode_from_roman(roman_numeral=roman)
        assert result["input_value"] == roman
        assert result["result"] == expected
        assert result["error"] is None


def test_decode_subtractive_combinations():
    """Test decoding Roman numerals with subtractive combinations."""
    test_cases = [
        ("IV", 4),  # 5-1
        ("IX", 9),  # 10-1
        ("XL", 40),  # 50-10
        ("XC", 90),  # 100-10
        ("CD", 400),  # 500-100
        ("CM", 900),  # 1000-100
    ]

    for roman, expected in test_cases:
        result = decode_from_roman(roman_numeral=roman)
        assert result["input_value"] == roman
        assert result["result"] == expected
        assert result["error"] is None


def test_decode_compound_numerals():
    """Test decoding compound Roman numerals."""
    test_cases = [
        ("III", 3),
        ("XIV", 14),
        ("XIX", 19),
        ("XXIV", 24),
        ("XLII", 42),
        ("XCIX", 99),
        ("CDXLIV", 444),
        ("CMXCIX", 999),
        ("MMXXIII", 2023),
        ("MMMCMXCIX", 3999),  # Maximum supported value
    ]

    for roman, expected in test_cases:
        result = decode_from_roman(roman_numeral=roman)
        assert result["input_value"] == roman
        assert result["result"] == expected
        assert result["error"] is None


def test_decode_lowercase_numerals():
    """Test decoding lowercase Roman numerals."""
    test_cases = [
        ("i", 1),
        ("iv", 4),
        ("x", 10),
        ("xlii", 42),
        ("mcdxliv", 1444),
    ]

    for roman, expected in test_cases:
        result = decode_from_roman(roman_numeral=roman)
        assert result["input_value"] == roman.upper()
        assert result["result"] == expected
        assert result["error"] is None


# --- Test Error Cases: Encoding ---


def test_encode_out_of_range():
    """Test encoding numbers outside the valid range (1-3999)."""
    # Test numbers that are too small
    result = encode_to_roman(number=0)
    assert result["input_value"] == 0
    assert result["result"] == ""
    assert result["error"] is not None
    assert "between 1 and 3999" in result["error"]

    # Test negative numbers
    result = encode_to_roman(number=-5)
    assert result["input_value"] == -5
    assert result["result"] == ""
    assert result["error"] is not None
    assert "between 1 and 3999" in result["error"]

    # Test numbers that are too large
    result = encode_to_roman(number=4000)
    assert result["input_value"] == 4000
    assert result["result"] == ""
    assert result["error"] is not None
    assert "between 1 and 3999" in result["error"]


# --- Test Error Cases: Decoding ---


def test_decode_invalid_characters():
    """Test decoding Roman numerals with invalid characters."""
    invalid_inputs = [
        "HELLO",  # English word
        "XII3",  # Mixed with digits
        "X I I",  # Spaces
        "IIIX",  # Invalid combination with X after III
        "IVIV",  # Invalid repetition of subtractive patterns
        "XM",  # X (10) before M (1000) is invalid
    ]

    for invalid_input in invalid_inputs:
        result = decode_from_roman(roman_numeral=invalid_input)
        assert result["input_value"].lower() == invalid_input.lower()
        assert result["error"] is not None


def test_decode_nonstandard_forms():
    """Test decoding Roman numerals in non-standard forms."""
    # These are technically parseable but aren't in the canonical form
    test_cases = [
        ("IIII", 4),  # Should be IV
        ("VIV", 9),  # Should be IX
        ("IIIIIIIII", 9),  # Should be IX
    ]

    for roman, expected in test_cases:
        result = decode_from_roman(roman_numeral=roman)
        assert result["input_value"].lower() == roman.lower()
        assert result["result"] == expected
        assert result["error"] is not None  # Should include warning
        assert "not in standard form" in result["error"].lower()


def test_decode_empty_input():
    """Test decoding an empty string."""
    result = decode_from_roman(roman_numeral="")
    assert result["input_value"] == ""
    assert result["result"] == 0
    assert result["error"] is not None


# --- Test Round Trip Conversions ---


def test_roundtrip_conversion():
    """Test round-trip conversion from decimal to Roman and back."""
    for num in [1, 4, 9, 14, 42, 99, 400, 999, 2023, 3999]:
        # Encode to Roman
        encoded = encode_to_roman(number=num)
        assert encoded["result"] != ""
        assert encoded["error"] is None

        # Decode back to decimal
        decoded = decode_from_roman(roman_numeral=encoded["result"])
        assert decoded["result"] == num
        assert decoded["error"] is None


# --- Edge Cases ---


def test_encoding_edge_values():
    """Test encoding the edge values of the supported range."""
    # Minimum supported value
    result = encode_to_roman(number=1)
    assert result["result"].lower() == "i"
    assert result["error"] is None

    # Maximum supported value
    result = encode_to_roman(number=3999)
    assert result["result"].lower() == "mmmcmxcix"
    assert result["error"] is None


def test_decoding_edge_cases():
    """Test decoding edge cases of Roman numerals."""
    # Single character
    result = decode_from_roman(roman_numeral="M")
    assert result["result"] == 1000
    assert result["error"] is None

    # Very long Roman numeral (represents 3888)
    result = decode_from_roman(roman_numeral="MMMDCCCLXXXVIII")
    assert result["result"] == 3888
    assert result["error"] is None
