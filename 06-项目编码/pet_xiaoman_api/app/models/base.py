from app.database import Base


class BaseModel(Base):
    __abstract__ = True
