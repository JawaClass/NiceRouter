from pydantic import BaseModel
from nicerouter.pydantic_util.asoptional import make_pydantic_model_optional

class Customer(BaseModel):
    id: int
    name: str

def print_model(model: type[BaseModel]):
    print(model)
    print(model.model_config) 
    print(model.model_fields)


def test():
    CustomerOptional = make_pydantic_model_optional(model=Customer)

    CustomerOptional_2 = make_pydantic_model_optional(model=Customer)

    print_model(CustomerOptional)
    print_model(CustomerOptional_2)



test()