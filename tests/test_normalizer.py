# from pprint import pformat

# from pydantic import BaseModel

# from nicerouter.normalization.normalizer import ObjectNormalizer


# class Customer(BaseModel):
#     id: int
#     name: str


# class Car(BaseModel):
#     id: int
#     name: str
#     owner: Customer | None
#     owner_id_xxx: int | None
#     prev_owners: list[Customer]


# # test that relationship can be uniquely linked to foreign key id field
# def test():
#     def ref2idfield_resolver(obj: BaseModel, field_name: str) -> str:
#         assert field_name == "owner"
#         print("ref2idfield_resolver.....", obj, "::::", field_name)
#         return "owner_id_xxx"

#     normalizer = ObjectNormalizer()
#     o = normalizer.normalize(
#         obj=Car(
#             id=1,
#             name="Rudoplh",
#             owner=Customer(id=1, name="Dudaf"),
#             owner_id_xxx=1,
#             prev_owners=[
#                 Customer(id=2, name="aaaaaaaaaaa"),
#                 Customer(id=3, name="bbbbb"),
#                 Customer(id=4, name="ccc"),
#             ],
#         ),
#         obj_model=Car,
#         ref2idfield_resolver=ref2idfield_resolver,
#     )

#     store = normalizer.store

#     assert "Customer" in store
#     assert "Car" in store

#     assert len(store["Customer"]) == 4
#     assert len(store["Car"]) == 1

#     store_after = {
#         "Car": {
#             1: {"id": 1, "name": "Rudoplh", "owner_id_xxx": 1, "prev_owners": [2, 3, 4]}
#         },
#         "Customer": {
#             1: {"id": 1, "name": "Dudaf"},
#             2: {"id": 2, "name": "aaaaaaaaaaa"},
#             3: {"id": 3, "name": "bbbbb"},
#             4: {"id": 4, "name": "ccc"},
#         },
#     }

#     assert pformat(dict(store)) == pformat(dict(store_after))


# if __name__ == "__main__":
#     test()
