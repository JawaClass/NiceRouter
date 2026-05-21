from nicerouter.routing.service.entity_mappers.mapper import ServiceEntityMapper
from nicerouter.routing.service.types import (
    EntiyType,
    InputType,
    OutputType,
)


class DefaultServiceEntityMapper[
    Entiy: EntiyType,
    Input: InputType,
    Output: OutputType,
](ServiceEntityMapper[Entiy, Input, Output, list[Output]]):
    def __init__(
        self,
        entity_cls: type[Entiy],
        input_cls: type[Input],
        output_cls: type[Output],
    ):
        self.entity_cls = entity_cls
        self.input_cls = input_cls
        self.output_cls = output_cls

    def input2entity(self, inp: Input) -> Entiy:
        entity = self.entity_cls(**inp.model_dump())
        return entity

    def entity2output(self, entity: Entiy) -> Output:
        output = self.output_cls.model_validate(entity)
        return output

    def entities2output(self, entities: list[Entiy]):
        output_many = [self.entity2output(entity) for entity in entities]
        return output_many
