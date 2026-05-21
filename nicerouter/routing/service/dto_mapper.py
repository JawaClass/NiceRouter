# from abc import ABC, abstractmethod
# from pydantic import BaseModel
# from sqlalchemy.orm import DeclarativeBase

# def check_dto_has_orm(dto_cls: type[BaseModel]):
#     if not dto_cls.model_config.get("from_attributes"):
#             raise TypeError(
#                 f"DTO {dto_cls.__name__} must have 'model_config = "
#                 "ConfigDict(from_attributes=True)' to map from a Database Entity."
#             )

# class EntityDtoMapper[T_DTO: BaseModel, T_ENTITY: DeclarativeBase](ABC):

#     def __init__(self, dto_cls: type[T_DTO], entity_cls: type[T_ENTITY]):
#         check_dto_has_orm(dto_cls)
#         self.dto_cls = dto_cls
#         self.entity_cls = entity_cls

#     @abstractmethod
#     def dto2entity(self, dto: T_DTO) -> T_ENTITY:
#         pass

#     @abstractmethod
#     def entity2dto(self, entity: T_ENTITY) -> T_DTO:
#         pass


# class EntityDtoMapperSameObjectImpl[T_DTO: BaseModel, T_ENTITY: DeclarativeBase](EntityDtoMapper[T_DTO, T_ENTITY]):

#     def dto2entity(self, dto: T_DTO) -> T_ENTITY:

#         entity = self.entity_cls(**dto.model_dump())
#         return entity

#     def entity2dto(self, entity: T_ENTITY) -> T_DTO:
#         dto = self.dto_cls.model_validate(entity)
#         return dto

