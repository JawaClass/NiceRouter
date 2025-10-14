from typing import Sequence
from pydantic import BaseModel, create_model, Field
from pydantic_core import PydanticUndefinedType
from nicerouter.normalization.type_util import is_reference_type, is_list_reference_type
from pprint import pprint
from nicerouter.type_utils import extract_most_inner_type

def normalize_type(model_class: type[BaseModel]) -> type[BaseModel]:
     
    model_fields = model_class.model_fields
 
    ref_fields = {
        field: field_info 
        for field, field_info in model_fields.items() 
        if is_reference_type(field_info.annotation)# type: ignore
    }
 
    list_fields = {
        field: field_info 
        for field, field_info in model_fields.items() 
        if is_list_reference_type(field_info.annotation)# type: ignore
    }

    primitive_fields = {
        field: field_info 
        for field, field_info in model_fields.items() 
        if field not in ref_fields and field not in list_fields
    }
    
    # fields as name 2 type
    normalized_fields = {}

    for field, field_info in primitive_fields.items(): 
        normalized_fields[field] = (field_info.annotation, field_info)
      
    for field in list_fields: 
       normalized_fields[field] = (list[int], Field())

    for field, field_info in ref_fields.items():  
        name = f"{field}_id"
        normalized_fields[name] = (int, Field(
            default=... if field_info.is_required() else None
            )) # field_info

    # Create a new model dynamically
    NewModel = create_model(
        f"Normalized_{model_class.__name__}",
        **normalized_fields,
        __base__=BaseModel,
        __module__="dynamic",
    )
    return NewModel

def build_normalized_store_type(
    model_class: type[BaseModel], 
) -> type[BaseModel]:
    normalized_fields = {}
    # start with self
    normalized_type_ = normalize_type(model_class=model_class) 
    name = model_class.__name__
    normalized_fields[name] = (dict[int, normalized_type_], Field(default_factory=dict))

    model_fields = model_class.model_fields
    for field, field_info in model_fields.items():

        inner_type = extract_most_inner_type(field_info.annotation) # type: ignore

        # print("build_normalized_response_model :: ", field, inner_type)
        if not is_reference_type(inner_type) and not is_list_reference_type(inner_type):
            continue

        normalized_type_ = normalize_type(model_class=inner_type) # type: ignore
        name = inner_type.__name__
         
        normalized_fields[name] = (dict[int, normalized_type_], Field(default_factory=dict))

    # Dynamically create a Pydantic model with these fields
    NormalizedModel = create_model(
        f"Normalized_Store_{model_class.__name__}",
        **normalized_fields,
        __module__="dynamic",
    )
    return NormalizedModel


if __name__ == "__main__":

    class Customer(BaseModel):
         
         id: int
         name: str

    class Car(BaseModel):
         
         id: int
         name: str
         optional_value: str | None
         owner: Customer | None
         prev_owners: list[Customer]

    t = normalize_type(model_class=Car)

    print(t)
    pprint(t.model_fields)
    
    t = build_normalized_store_type(model_class=Car)
    print(t)
    pprint(t.model_fields)