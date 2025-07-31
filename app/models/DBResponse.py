
from pydantic import BaseModel


class ResponseMetadataModel(BaseModel):
    HTTPStatusCode: int


class DBResponse(BaseModel):
    ResponseMetadata: ResponseMetadataModel
