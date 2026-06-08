from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models import (
    Destination,
    Diary,
    Facility,
    Food,
    IndoorEdge,
    IndoorNode,
    Restaurant,
    User,
    UserBehaviorLog,
    UserFavorite,
    UserRating,
)
from app.services.amap_import_service import AMapPoiImportError, import_amap_pois_to_db
from app.services.osm_import_service import (
    OsmImportError,
    build_osmnx_payload,
    get_map_import_status,
    import_fixture_osm_payload,
    import_osm_payload_to_db,
)

router = APIRouter()


class MapImportRequest(BaseModel):
    source: str = Field(default="fixture", description="fixture, osmnx, or amap_poi")
    place_name: str | None = Field(default=None)
    center_lng: float | None = Field(default=None)
    center_lat: float | None = Field(default=None)
    dist: int | None = Field(default=None, ge=100, le=10000)
    keywords: list[str] | None = Field(default=None)
    max_pages: int = Field(default=3, ge=1, le=20)
    request_interval: float = Field(default=0.3, ge=0, le=5)
    reset_existing: bool = Field(default=True)


@router.get("/stats")
def admin_stats(db: Session = Depends(get_db)) -> dict:
    return {
        "map": get_map_import_status(db),
        "tables": {
            "users": _count(db, User),
            "user_favorites": _count(db, UserFavorite),
            "user_ratings": _count(db, UserRating),
            "user_behavior_logs": _count(db, UserBehaviorLog),
            "destinations": _count(db, Destination),
            "facilities": _count(db, Facility),
            "restaurants": _count(db, Restaurant),
            "foods": _count(db, Food),
            "diaries": _count(db, Diary),
            "indoor_nodes": _count(db, IndoorNode),
            "indoor_edges": _count(db, IndoorEdge),
        },
    }


@router.get("/map/import/status")
def map_import_status(db: Session = Depends(get_db)) -> dict:
    return get_map_import_status(db)


@router.post("/map/import")
def import_map(payload: MapImportRequest, db: Session = Depends(get_db)) -> dict:
    try:
        if payload.source == "fixture":
            return import_fixture_osm_payload(db, reset_existing=payload.reset_existing)
        if payload.source == "osmnx":
            osm_payload = build_osmnx_payload(
                place_name=payload.place_name or settings.osm_default_place,
                center_lng=payload.center_lng or settings.osm_fallback_lng,
                center_lat=payload.center_lat or settings.osm_fallback_lat,
                dist=payload.dist or settings.osm_fallback_dist,
            )
            return import_osm_payload_to_db(db, osm_payload, reset_existing=payload.reset_existing)
        if payload.source == "amap_poi":
            return import_amap_pois_to_db(
                session=db,
                api_key=settings.amap_web_api_key or "",
                center_lng=payload.center_lng or settings.osm_fallback_lng,
                center_lat=payload.center_lat or settings.osm_fallback_lat,
                radius=payload.dist or settings.osm_fallback_dist,
                keywords=payload.keywords,
                max_pages=payload.max_pages,
                reset_facilities=payload.reset_existing,
                request_interval=payload.request_interval,
            )
    except AMapPoiImportError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except OsmImportError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Map import failed: {exc}") from exc

    raise HTTPException(status_code=400, detail="Unsupported import source.")


def _count(db: Session, model) -> int:
    return int(db.scalar(select(func.count()).select_from(model)) or 0)
