from sqlmodel import Session, select
from fastapi import HTTPException
from ..models import Item
from ..schemas import ItemCreate, ItemUpdate

def create_item(session: Session, data: ItemCreate) -> Item:
    obj = Item(name=data.name, description=data.description)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj

def list_items(session: Session, limit: int, offset: int) -> list[Item]:
    return session.exec(select(Item).offset(offset).limit(limit)).all()

def get_item(session: Session, item_id: int) -> Item:
    obj = session.get(Item, item_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Item not found")
    return obj

def update_item(session: Session, item_id: int, data: ItemUpdate) -> Item:
    obj = session.get(Item, item_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Item not found")
    if data.name is not None:
        obj.name = data.name
    if data.description is not None:
        obj.description = data.description
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj

def delete_item(session: Session, item_id: int) -> None:
    obj = session.get(Item, item_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Item not found")
    session.delete(obj)
    session.commit()
