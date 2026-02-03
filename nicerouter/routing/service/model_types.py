from pydantic import BaseModel
from typing import Sequence

class BatchItem_ContainerType[T_ID: object, T_DATA: BaseModel](BaseModel):
        id: T_ID
        data: T_DATA


class BatchInputModel_ContainerType[T_ID: object, T_DATA: BaseModel](BaseModel):
        items: Sequence[BatchItem_ContainerType[T_ID, T_DATA]]

