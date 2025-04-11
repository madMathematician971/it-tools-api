from pydantic import BaseModel, Field


class CaseConvertInput(BaseModel):
    input: str
    target_case: str = Field(
        ...,
        description="Target case (e.g., camel, snake, pascal, constant, kebab, capital, dot, header, sentence, path, lower, upper)",
    )


class CaseConvertOutput(BaseModel):
    result: str
