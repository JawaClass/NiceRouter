from nicerouter.normalization.normalizer import ObjectNormalizer
from pydantic import BaseModel
from pprint import pprint, pformat

class Customer(BaseModel):        
        id: int
        name: str

class Car(BaseModel):
        id: int
        name: str
        owner: Customer | None
        prev_owners: list[Customer]

def test():
    normalizer = ObjectNormalizer()
    o = normalizer.normalize(obj=Car(id=1, name="Rudoplh", owner=Customer(id=1, name="Dudaf"), prev_owners=[
            Customer(id=2, name="aaaaaaaaaaa"),
            Customer(id=3, name="bbbbb"),
            Customer(id=4, name="ccc")

    ]))

    store = normalizer.store

    assert "Customer" in store
    assert "Car" in store

    assert len(store["Customer"]) == 4
    assert len(store["Car"]) == 1
  
    store_after =  {'Car': {1: {'id': 1,
                         'name': 'Rudoplh',
                         'owner_id': 1,
                         'prev_owners': [2, 3, 4]}},
             'Customer': {1: {'id': 1, 'name': 'Dudaf'},
                          2: {'id': 2, 'name': 'aaaaaaaaaaa'},
                          3: {'id': 3, 'name': 'bbbbb'},
                          4: {'id': 4, 'name': 'ccc'}}}
    
    assert pformat(dict(store)) == pformat(dict(store_after))
 

if __name__ == "__main__":
       
       test()