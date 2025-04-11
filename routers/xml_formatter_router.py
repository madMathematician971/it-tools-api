import logging
import xml.dom.minidom
import xml.etree.ElementTree as ET
from xml.parsers.expat import ExpatError

from fastapi import APIRouter, HTTPException, status

from models.xml_formatter_models import XmlInput, XmlOutput

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/xml-formatter", tags=["XML Formatter"])


@router.post("/", response_model=XmlOutput)
async def format_xml(input_data: XmlInput):
    """Format/prettify XML with custom indentation."""
    try:
        xml_str = input_data.xml.strip()
        if not xml_str:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="XML string cannot be empty")

        # Format XML using minidom or ElementTree based on settings
        try:
            if input_data.preserve_whitespace:
                # Use minidom to preserve whitespace
                dom = xml.dom.minidom.parseString(xml_str)
                formatted_bytes = dom.toprettyxml(indent=input_data.indent, encoding=input_data.encoding)
                formatted = formatted_bytes.decode(input_data.encoding)

                # Optionally remove XML declaration
                if input_data.omit_declaration:
                    lines = formatted.split("\n")
                    if lines and "<?xml" in lines[0]:
                        formatted = "\n".join(lines[1:]).lstrip()
            else:
                # Use ElementTree for better formatting control
                root = ET.fromstring(xml_str)
                ET.indent(root, space=input_data.indent)

                # Format with XML declaration
                if not input_data.omit_declaration:
                    formatted = ET.tostring(root, encoding=input_data.encoding, xml_declaration=True).decode(
                        input_data.encoding
                    )
                else:
                    # Format without XML declaration
                    formatted = ET.tostring(root, encoding=input_data.encoding, xml_declaration=False).decode(
                        input_data.encoding
                    )

            return XmlOutput(original=xml_str, formatted=formatted)

        except (ExpatError, ET.ParseError) as xml_err:
            return XmlOutput(original=xml_str, formatted="", error=f"Invalid XML: {str(xml_err)}")

    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        logger.error(f"Error formatting XML: {e}", exc_info=True)
        original_xml = input_data.xml if input_data else ""
        return XmlOutput(original=original_xml, formatted="", error=f"Failed to format XML: {str(e)}")
