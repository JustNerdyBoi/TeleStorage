import sqlalchemy
from .db_session import SqlAlchemyBase


class Chunk(SqlAlchemyBase):
    __tablename__ = 'chunks'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    file_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("files.id"))

    chat_file_id = sqlalchemy.Column(sqlalchemy.String)
    file_name = sqlalchemy.Column(sqlalchemy.String)

    token = sqlalchemy.Column(sqlalchemy.String)