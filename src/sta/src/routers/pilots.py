from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from src import models, schemas
from src.settings import settings
from src.sparql.cached_properties_handler import CachedPropertiesHandler
from src.utils import get_db

router = APIRouter(tags=["Pilots"])


def get_pilot_schema(request: Request, db_pilot):
    if settings.DEBUG:
        url = f"{settings.HTTP}{request.url.netloc}/{db_pilot.name}/api/v1.0/"
    else:
        url = f"{settings.HTTPS}{request.url.netloc}/{db_pilot.name}/api/v1.0/"
    pilot = schemas.PilotResponse(
        name=db_pilot.name,
        description=db_pilot.description,
        custom_endpoint=db_pilot.custom_endpoint,
        rootURL=url,
        swaggerURL=f"{url}docs",
        graphs=db_pilot.graphs,
    )

    return pilot


@router.get("/pilots", response_model=list[schemas.PilotResponse])
def read_pilots(request: Request, top: int = 100, skip: int = 0, db: Session = Depends(get_db)):
    db_pilots = db.query(models.Pilot).offset(skip).limit(top).all()
    pilot_schemas = []
    for db_pilot in db_pilots:
        pilot_scheme = get_pilot_schema(request, db_pilot)
        pilot_schemas.append(pilot_scheme)

    return pilot_schemas


@router.post("/pilots", response_model=schemas.PilotResponse)
def create_pilot(request: Request, new_pilot_data: schemas.Pilot, db: Session = Depends(get_db)):
    db_pilot = db.query(models.Pilot).filter(models.Pilot.name == new_pilot_data.name).first()
    if db_pilot:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Pilot with name {new_pilot_data.name} already exists"
        )
    pilot = models.Pilot(**new_pilot_data.model_dump())
    db.add(pilot)
    db.commit()

    pilot_scheme = get_pilot_schema(request, pilot)

    return pilot_scheme


@router.get("/pilots/{name}", response_model=schemas.PilotResponse)
def read_pilot(request: Request, name: str, db: Session = Depends(get_db)):
    db_pilot = db.query(models.Pilot).filter(models.Pilot.name == name).first()
    if not db_pilot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Pilot with name {name} not found")

    pilot_scheme = get_pilot_schema(request, db_pilot)

    return pilot_scheme


@router.put("/pilots/{name}", response_model=schemas.PilotResponse)
def update_pilot(
    request: Request, name: str, updated_pilot_data: schemas.Pilot, response: Response, db: Session = Depends(get_db)
):
    db_pilot = db.query(models.Pilot).filter(models.Pilot.name == name).first()
    if db_pilot:
        db_pilot.name = updated_pilot_data.name
        db_pilot.description = updated_pilot_data.description
        db_pilot.custom_endpoint = updated_pilot_data.custom_endpoint
        db_pilot.graphs = updated_pilot_data.graphs
        db.commit()

        pilot_scheme = get_pilot_schema(request, db_pilot)

        return pilot_scheme
    else:
        pilot = models.Pilot(**updated_pilot_data.model_dump())
        db.add(pilot)
        db.commit()
        response.status_code = status.HTTP_201_CREATED

        pilot_scheme = get_pilot_schema(request, pilot)

        return pilot_scheme


@router.post("/pilots/cache/{name}")
def cache_pilot(name: str, db: Session = Depends(get_db)):
    db_pilot = db.query(models.Pilot).filter(models.Pilot.name == name).first()

    if db_pilot:
        handler = CachedPropertiesHandler(db_pilot)
        db_pilot.cached_properties = handler.get_integer_code()
        db.commit()
        return JSONResponse(status_code=status.HTTP_200_OK, content={"status": "Cache reloaded successfully!"})
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Pilot with name {name} doesn't exists")


@router.delete("/pilots/{name}")
def delete_pilot(name: str, response: Response, db: Session = Depends(get_db)):
    db_pilot = db.query(models.Pilot).filter(models.Pilot.name == name).first()
    if db_pilot:
        db.delete(db_pilot)
        db.commit()
        response.status_code = status.HTTP_204_NO_CONTENT
        return response
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Pilot with name {name} doesn't exists")
