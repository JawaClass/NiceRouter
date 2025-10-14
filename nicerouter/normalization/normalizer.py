from collections import defaultdict
from typing import Any, Callable, Sequence, get_origin
from pydantic import BaseModel 
from nicerouter.type_utils import extract_most_inner_type
from nicerouter.normalization.type_util import is_list_reference_type, is_reference_type


class ObjectNormalizer:

    def __init__(self) -> None:
         self.store = defaultdict(dict)
        
    def normalize(
            self,
            *,
            obj: BaseModel,
            id_name: str = "id",
        ) -> dict[str, Any]:
            
            # get or create slice for this type
            store_slice = self.store[obj.__class__.__name__]

            # return early if its already normalized
            id = getattr(obj, id_name)
            if id in store_slice:
                 return store_slice[id]
            
            model_fields = type(obj).model_fields

            normalized_obj = obj.model_dump(mode="python", exclude_none=False)

            reference_fields = {
                field_name: field_info for 
                field_name, field_info in model_fields.items()
                if is_reference_type(field_info.annotation) # type: ignore
            }

            list_fields = {
                field_name: field_info for 
                field_name, field_info in model_fields.items()
                if is_list_reference_type(field_info.annotation) # type: ignore
            }
 
            for field_name in reference_fields:
                
                ref_field_obj = getattr(obj, field_name)

                if ref_field_obj is None:
                    # setattr(normalized_obj, field_name, None)
                    normalized_obj[field_name] = None
                    continue
                  
                id_field = f"{field_name}_id"
                assert id_field in normalized_obj, f"Object doesnt have attribute {id_field} from reference field {field_name}"
                self.normalize(obj=ref_field_obj, id_name=id_name)
                normalized_obj[id_field] = normalized_obj[field_name][id_name]
                del normalized_obj[field_name]

            for field_name in list_fields: 
 
                # normalize and set list of ids field as part of normalized entity
                normalized_obj[field_name] = [
                    self.normalize(obj=o)[id_name] for o in getattr(obj, field_name)
                ]

            # store normalized object in slice
            store_slice[id] = normalized_obj

            return normalized_obj

 