# app/services/
**Qué va aquí:** lógica de negocio reutilizable, sin detalles de HTTP.
**Ventaja:** testear servicios sin levantar FastAPI.
**Ejemplo:** `items.py` contiene create/list/get/update/delete sobre `Item`.
