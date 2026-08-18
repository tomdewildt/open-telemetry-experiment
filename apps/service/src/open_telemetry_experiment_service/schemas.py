from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class ProcessRequest(BaseSchema):
    text: str = Field(min_length=1, description="Text to process.")


class ProcessResponse(BaseSchema):
    result: str
    word_count: int
