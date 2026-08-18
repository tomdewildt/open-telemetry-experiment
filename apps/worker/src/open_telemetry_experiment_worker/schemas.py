from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class JobRequest(BaseSchema):
    request_id: str = Field(min_length=1, description="Caller-provided request identifier.")
    text: str = Field(min_length=1, description="Text to process.")
    callback_url: str = Field(min_length=1, description="URL called with the result once the job is done.")


class JobResponse(BaseSchema):
    job_id: str
