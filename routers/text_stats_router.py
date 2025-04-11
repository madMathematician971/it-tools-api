import re

from fastapi import APIRouter, HTTPException, status

from models.text_stats_models import TextStatsInput, TextStatsOutput

router = APIRouter(prefix="/api/text", tags=["Text"])


@router.post("/stats", response_model=TextStatsOutput)
async def calculate_text_stats(payload: TextStatsInput):
    """Calculate various statistics for the input text."""
    try:
        text = payload.text

        char_count = len(text)
        char_count_no_spaces = len("".join(text.split()))  # More concise way

        words = text.split()
        word_count = len(words)

        lines = text.splitlines()
        # Count non-empty lines if desired, or just total lines
        line_count = len(lines)
        # non_empty_line_count = len([line for line in lines if line.strip()])

        # Improved Sentence count using lookahead for better splitting
        sentences = re.split(r"(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s", text)
        sentence_count = len([s for s in sentences if s.strip()])
        if sentence_count == 0 and len(text.strip()) > 0:
            sentence_count = 1

        paragraphs = re.split(r"\n\s*\n", text)
        paragraph_count = len([p for p in paragraphs if p.strip()])
        if paragraph_count == 0 and len(text.strip()) > 0:
            paragraph_count = 1

        stats = {
            "char_count": char_count,
            "char_count_no_spaces": char_count_no_spaces,
            "word_count": word_count,
            "line_count": line_count,
            "sentence_count": sentence_count,
            "paragraph_count": paragraph_count,
        }

        return TextStatsOutput(stats=stats)

    except Exception as e:
        print(f"Error calculating text stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during text stats calculation",
        )
