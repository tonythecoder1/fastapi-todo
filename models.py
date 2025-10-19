from pydantic import BaseModel
from database import Base
import sqlalchemy as sa

import sqlalchemy as sa
from database import Base

class Users(Base):
    __tablename__ = "users"

    id = sa.Column(sa.Integer, primary_key=True, index=True)
    username = sa.Column(sa.String, unique=True, nullable=False)
    email = sa.Column(sa.String, unique=True, nullable=False)
    first_name = sa.Column(sa.String)
    last_name = sa.Column(sa.String)
    role = sa.Column(sa.String)
    hashed_password = sa.Column(sa.String)
    is_active = sa.Column(sa.Boolean, default=True)


class Todos(Base):
    __tablename__= 'todos'
    
    id = sa.Column(sa.Integer, primary_key=True, index=True)
    title = sa.Column(sa.String)
    description = sa.Column(sa.String)
    priority = sa.Column(sa.Integer)
    complete = sa.Column(sa.Boolean)
    owner_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"))
    
    
