from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Any

from beanie import Document


T = TypeVar("T", bound=Document)    

# тут очень крутая бурмалда для динамической подстановки модели в классах-наследователях # ничесе
class RepositoryABC(ABC, Generic[T]):
    model: type[T]

    async def create(self, **kwargs) -> T:
        instance = self.model(**kwargs)
        await instance.save()
        return instance

    async def get_by_id(self, entity_id: int) -> T | None:
        return await self.model.get(entity_id)

    async def delete(self, entity: T) -> None:
        await entity.delete()

    async def change_field(
            self,
            id_: int,
            field: str,
            value: Any,
        ) -> None:
            await self.model.find_one(
                self.model.id == id_
            ).update(
                {
                    "$set": {
                        field: value,
                    }
                }
            )

    async def get_all(
        self, 
        **kwargs
    ) -> list[T]:
        messages = await self.model.find(kwargs).to_list()
        return messages