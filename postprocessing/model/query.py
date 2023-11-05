from typing import Union

from fastapi import FastAPI
from pydantic import BaseModel


class Query(BaseModel):
    image: Union[str, None] = None
    postprocess_config: Union[dict, None] = None
    topic_name: Union[str, None] = None
    metadata: Union[dict, None] = None
    boundary_config: Union[dict, None] = None
