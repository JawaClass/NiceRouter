from collections import defaultdict
from functools import cache
from typing import Any, Callable

from pydantic import BaseModel

from nicerouter.normalization.type_util import is_list_reference_type, is_reference_type
from nicerouter.type_utils import extract_most_inner_type

type IdResolver = Callable[[BaseModel, str], str]


class ObjectNormalizer:
    def __init__(
        self,
        # pass an optional callback to link a reference field to the correct id field when its
        # not called {reference_field}_id
        ref2idfield_resolver: IdResolver | None = None,
    ):
        self.ref2idfield_resolver = ref2idfield_resolver
        self.store = defaultdict(dict)

    @cache
    def _is_reference_type(self, x):
        rt = is_reference_type(x)
        # print("is_reference_type", x, rt)
        return rt

    @cache
    def _is_list_reference_type(self, x):
        return is_list_reference_type(x)

    @cache
    def _extract_most_inner_type(self, model: type[BaseModel], field_name: str):
        field_info = model.model_fields.get(field_name)
        if field_info is None:
            raise ValueError(
                f"{model=}:{field_info=}. field_info was None. Not sure how to handle this."
            )
        annotation = field_info.annotation
        if annotation is None:
            raise ValueError(
                f"{model=}:{field_info=}. annotation was None. Not sure how to handle this."
            )
        return extract_most_inner_type(annotation)

    @cache
    def _get_model_metadata(self, model_type: type[BaseModel]):
        model_fields = model_type.model_fields

        reference_fields = {
            field_name: field_info
            for field_name, field_info in model_fields.items()
            if self._is_reference_type(field_info.annotation)  # type: ignore
        }

        list_fields = {
            field_name: field_info
            for field_name, field_info in model_fields.items()
            if self._is_list_reference_type(field_info.annotation)  # type: ignore
        }

        # 3. Identify Standard Fields (Scalars) to copy directly
        # We exclude refs and lists so we don't dump them unnecessarily
        standard = (
            set(model_fields.keys())
            - set(reference_fields.keys())
            - set(list_fields.keys())
        )

        return reference_fields, list_fields, standard

    # def relationhsip_available(self, relationship: str):
    #      if "addresses" not in inspect(user).unloaded:
    #      ...

    def normalize(
        self,
        *,
        obj: object,
        obj_model: type[BaseModel],
        id_name: str = "id",
        ref2idfield_resolver: IdResolver | None = None,
    ) -> dict[str, Any]:
        ref2idfield_resolver = ref2idfield_resolver or self.ref2idfield_resolver
        # get or create slice for this type
        slicename = obj_model.__name__
        store_slice = self.store[slicename]

        # return early if its already normalized
        id = getattr(obj, id_name)
        if id in store_slice:
            return store_slice[id]

        reference_fields, list_fields, standard_fields = self._get_model_metadata(
            obj_model
        )

        # normalized_obj = obj.model_dump(mode="python", exclude_none=False)
        normalized_obj = {k: getattr(obj, k) for k in standard_fields}

        field_names_with_detached_error: set[str] = set()

        # normalize ref children
        for field_name in reference_fields:
            # dont raise lazy load error on not loaded fields
            if field_name not in obj.__dict__:
                normalized_obj[field_name] = None
                continue

            # try:
            ref_field_obj = getattr(obj, field_name)
            # except DetachedInstanceError:
            #     print("ADD DETACHED", field_name)
            #     field_names_with_detached_error.add(field_name)
            #     continue

            if ref_field_obj is None:
                normalized_obj[field_name] = None
                continue

            # check if reference field is linked by expected id field name
            # otherwise, try resolve it
            id_field = f"{field_name}_id"
            if id_field not in normalized_obj:
                if (
                    not ref2idfield_resolver
                    and field_name not in field_names_with_detached_error
                ):
                    print(":::::::::::", field_name, field_names_with_detached_error)
                    msg = f"Object {type(obj)}(...) doesnt have attribute {id_field} from reference field {field_name}. Add resolver argument."
                    raise ValueError(msg)
                id_field = ref2idfield_resolver(obj, field_name)

            # normalize child
            ref_field_obj_model = self._extract_most_inner_type(obj_model, field_name)

            normalized_child = self.normalize(
                obj=ref_field_obj, obj_model=ref_field_obj_model, id_name=id_name
            )
            # set id field with id of child
            normalized_obj[id_field] = normalized_child[id_name]

        # normalize ref children inside list
        for field_name in list_fields:
            # dont raise lazy load error on not loaded fields
            if field_name not in obj.__dict__:
                normalized_obj[field_name] = []
                continue

            ref_field_obj_model = self._extract_most_inner_type(obj_model, field_name)

            # try:
            normalized_obj[field_name] = [
                self.normalize(obj=o, obj_model=ref_field_obj_model)[id_name]
                for o in getattr(obj, field_name)
            ]
            # except DetachedInstanceError:
            #     # print("ADD DETACHED", field_name)
            #     field_names_with_detached_error.add(field_name)
            #     normalized_obj[field_name] = []
            #     continue

        # store normalized object in slice
        store_slice[id] = normalized_obj

        return normalized_obj
