from fastapi import APIRouter, Depends
from sqlmodel import Session
from ..db import get_session
from ..schemas import ItemCreate, ItemUpdate, ItemRead
from ..services import items as svc

router = APIRouter()

@router.post("", response_model=ItemRead)
def create(payload: ItemCreate, session: Session = Depends(get_session)):
    return svc.create_item(session, payload)

@router.get("", response_model=list[ItemRead])
def list_(limit: int = 10, offset: int = 0, session: Session = Depends(get_session)):
    return svc.list_items(session, limit, offset)

@router.get("/{item_id}", response_model=ItemRead)
def retrieve(item_id: int, session: Session = Depends(get_session)):
    return svc.get_item(session, item_id)

@router.put("/{item_id}", response_model=ItemRead)
def update(item_id: int, payload: ItemUpdate, session: Session = Depends(get_session)):
    return svc.update_item(session, item_id, payload)

@router.delete("/{item_id}", status_code=204)
def delete(item_id: int, session: Session = Depends(get_session)):
    svc.delete_item(session, item_id)
