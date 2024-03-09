import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase


class File(SqlAlchemyBase):
    __tablename__ = 'files'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    owner_id = orm.relationship('User')

    chunks = orm.relationship("Chunk", back_populates='file_id')

    public = sqlalchemy.Column(sqlalchemy.Boolean, default=False)