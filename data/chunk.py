import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase


class Chunk(SqlAlchemyBase):
    __tablename__ = 'chunks'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    file_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("files.id"))

    chat_id = sqlalchemy.Column(sqlalchemy.Integer)
    message_id = sqlalchemy.Column(sqlalchemy.Integer)

    chunk_number = sqlalchemy.Column(sqlalchemy.Integer)