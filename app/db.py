from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import event

ENGINE = create_engine("sqlite:///./app.db", echo=False)

def init_db():
    SQLModel.metadata.create_all(ENGINE)



@event.listens_for(ENGINE, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()


def get_session():
    with Session(ENGINE) as session:
        yield session
