# flake8: noqa
from fastapi import FastAPI, status

# Import future routers here...
# Import routers (ensure these files exist in ./routers/)
from routers import (
    ascii_text_drawer_router,
    base64_router,
    base_converter_router,
    basic_auth_router,
    bcrypt_router,
    bip39_router,
    case_converter_router,
    chmod_router,
    color_converter_router,
    cron_router,
    data_converter_router,
    datetime_router,
    docker_router,
    email_router,
    encryption_router,
    eta_router,
    hash_router,
    hmac_router,
    html_entities_router,
    iban_router,
    ipv4_converter_router,
    ipv4_range_expander_router,
    ipv4_subnet_router,
    ipv6_ula_router,
    json_csv_converter_router,
    json_diff_router,
    json_router,
    jwt_router,
    list_converter_router,
    lorem_router,
    mac_address_lookup_router,
    markdown_router,
    math_eval_router,
    meta_tag_generator_router,
    mime_router,
    nato_alphabet_router,
    numeronym_router,
    password_strength_router,
    pdf_signature_checker_router,
    percentage_router,
    phone_router,
    qrcode_router,
    random_port_router,
    regex_router,
    roman_numeral_router,
    rsa_router,
    safelink_decoder_router,
    slugify_router,
    sql_formatter_router,
    string_obfuscator_router,
    svg_placeholder_router,
    temperature_router,
    text_binary_router,
    text_diff_router,
    text_stats_router,
    token_router,
    ulid_router,
    unicode_converter_router,
    url_encoder_router,
    url_parser_router,
    user_agent_parser_router,
    uuid_router,
    xml_formatter_router,
)

app = FastAPI(
    title="IT Tools API (Python)",
    description="Standalone API replicating IT Tools functionality.",
    version="0.1.0",
)


# --- Health Check Endpoint ---
@app.get("/api/health", tags=["Health"], status_code=status.HTTP_200_OK)
async def health_check():
    """Check if the API is running."""
    return {"status": "ok", "message": "API is running"}


# --- Include Tool Routers ---
app.include_router(base64_router.router)
app.include_router(basic_auth_router.router)
app.include_router(ascii_text_drawer_router.router)
app.include_router(bcrypt_router.router)
app.include_router(bip39_router.router)
app.include_router(case_converter_router.router)
app.include_router(chmod_router.router)
app.include_router(color_converter_router.router)
app.include_router(cron_router.router)
app.include_router(data_converter_router.router)
app.include_router(datetime_router.router)
app.include_router(docker_router.router)
app.include_router(email_router.router)
app.include_router(encryption_router.router)
app.include_router(hash_router.router)
app.include_router(hmac_router.router)
app.include_router(html_entities_router.router)
app.include_router(iban_router.router)
app.include_router(base_converter_router.router)
app.include_router(ipv4_subnet_router.router)
app.include_router(json_router.router)
app.include_router(jwt_router.router)
app.include_router(lorem_router.router)
app.include_router(markdown_router.router)
app.include_router(math_eval_router.router)
app.include_router(mime_router.router)
app.include_router(percentage_router.router)
app.include_router(phone_router.router)
app.include_router(qrcode_router.router)
app.include_router(regex_router.router)
app.include_router(rsa_router.router)
app.include_router(slugify_router.router)
app.include_router(sql_formatter_router.router)
app.include_router(temperature_router.router)
app.include_router(text_stats_router.router)
app.include_router(token_router.router)
app.include_router(uuid_router.router)
app.include_router(url_encoder_router.router)
app.include_router(url_parser_router.router)
app.include_router(user_agent_parser_router.router)
app.include_router(text_binary_router.router)
app.include_router(nato_alphabet_router.router)
app.include_router(unicode_converter_router.router)
app.include_router(roman_numeral_router.router)
app.include_router(ulid_router.router)
app.include_router(eta_router.router)
app.include_router(ipv4_converter_router.router)
app.include_router(ipv4_range_expander_router.router)
app.include_router(list_converter_router.router)
app.include_router(mac_address_lookup_router.router)
app.include_router(password_strength_router.router)
app.include_router(random_port_router.router)
app.include_router(safelink_decoder_router.router)
app.include_router(string_obfuscator_router.router)
app.include_router(text_diff_router.router)
app.include_router(json_csv_converter_router.router)
app.include_router(meta_tag_generator_router.router)
app.include_router(numeronym_router.router)
app.include_router(svg_placeholder_router.router)
app.include_router(xml_formatter_router.router)
app.include_router(ipv6_ula_router.router)
app.include_router(json_diff_router.router)
app.include_router(pdf_signature_checker_router.router)
