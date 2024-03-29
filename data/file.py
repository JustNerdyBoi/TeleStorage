import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase


class File(SqlAlchemyBase):
    __tablename__ = 'files'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))

    public = sqlalchemy.Column(sqlalchemy.Boolean, default=False)