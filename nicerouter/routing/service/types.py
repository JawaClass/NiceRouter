from typing import Any

from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase

type EntiyType = DeclarativeBase

type InputType = BaseModel

type OutputType = BaseModel

type OutputManyType = Any
