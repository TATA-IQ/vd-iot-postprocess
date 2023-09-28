from fastapi import FastAPI
from pydantic import BaseModel
from typing import Union
class Query(BaseModel):
    image: Union[str, None] = None
    postprocess_config: Union[dict, None] = None
    topic_name: Union[str, None] = None
    metadata: Union[dict, None] = None