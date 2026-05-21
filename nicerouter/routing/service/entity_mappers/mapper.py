from abc import ABC, abstractmethod

from nicerouter.routing.service.types import (
    EntiyType,
    InputType,
    OutputManyType,
    OutputType,
)


class ServiceEntityMapper[
    Entiy: EntiyType,
    Input: InputType,
    Output: OutputType,
    OutputMany: OutputManyType,
](ABC):
    def __init__(
        self,
        entity_cls: type[Entiy],
        input_cls: type[Input],
        output_cls: type[Output],
        output_many_cls: type[OutputMany],
    ):
        self.entity_cls = entity_cls
        self.input_cls = input_cls
        self.output_cls = output_cls
        self.output_many_cls = output_many_cls

    @abstractmethod
    def input2entity(self, inp: Input) -> Entiy: ...

    @abstractmethod
    def entity2output(self, entity: Entiy) -> Output: ...

    @abstractmethod
    def entities2output(self, entities: list[Entiy]) -> OutputMany: ...
