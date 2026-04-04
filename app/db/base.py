# app/db/base.py

# DeclarativeBase is the foundation that all our models inherit from.
# When SQLAlchemy sees a class that inherits from Base,
# it knows "this class represents a database table".

from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass