from typing import Any, ForwardRef, get_args

def extract_most_inner_type(annotation: type[Any]):
    a = annotation
    prev = a
    while a is not None:
        prev = a
        a = extract_inner_type(a)
        print("a", a)
    return prev

def extract_inner_type_or_self(annotation: type[Any]):
    a = extract_inner_type(annotation)
    return a if a is not None else annotation

def extract_inner_type(annotation: type[Any]):
   
    if isinstance(annotation, ForwardRef):
        msg = f"""Cannot resolve ForwardRef annotation {annotation}.
        "Please resolve it before calling this method.
        "When its an pydantic model consider model_rebuild"""
        raise TypeError(msg)

    args = get_args(annotation)
    args = [a for a in args if a is not type(None)]
    
    if len(args) == 0:
        return None
    if len(args) == 1:
        return args[0]

    return None


if __name__ == "__main__":
    assert extract_inner_type(str) is None
    assert extract_inner_type_or_self(str) is str
    
    err = None
    try:
        extract_inner_type(ForwardRef("aaaa")) # type:ignore
    except TypeError as e:
        err = e
    assert isinstance(err, TypeError)  
    assert extract_inner_type_or_self(int) is int
    assert extract_inner_type(list[int]) is int
    assert extract_inner_type(list[list[int]]) == list[int]
    assert extract_inner_type_or_self(str) is str
    assert extract_most_inner_type(list[int]) is int
    
    assert extract_most_inner_type(list[list[int]]) is int

    class A:
        pass

    assert extract_inner_type_or_self(A) is A

    