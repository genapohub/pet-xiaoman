import enum
from sqlalchemy import String, Integer, Enum, DECIMAL, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import StoreScopedModel


class Species(str, enum.Enum):
    DOG = "犬"
    CAT = "猫"
    RABBIT = "兔"
    OTHER = "其他"


class Pet(StoreScopedModel):
    __tablename__ = "pets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(30))
    species: Mapped[Species] = mapped_column(Enum(Species), default=Species.DOG)
    weight: Mapped[float | None] = mapped_column(DECIMAL(4, 1))  # kg，影响火化计价
    owner_id: Mapped[int] = mapped_column(Integer, index=True)
    deleted: Mapped[bool] = mapped_column(Boolean, default=False)  # 档案软删
