from sqlmodel import SQLModel, create_engine, Session

ENGINE = create_engine("sqlite:///./app.db", echo=False)

def init_db():
    SQLModel.metadata.create_all(ENGINE)

def get_session():
    with Session(ENGINE) as session:
        yield session
