from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.backend.db.database import get_db
from app.backend.db.models import SiiCommuneModel, SiiRegionModel

sii_geo = APIRouter(prefix="/sii", tags=["SII Geo"])


@sii_geo.get("/regions")
def list_sii_regions(db: Session = Depends(get_db)):
    """Catálogo regiones SII BTE. Shape compatible con selects (id + region)."""
    rows = db.query(SiiRegionModel).order_by(SiiRegionModel.id).all()
    return {
        "message": [
            {
                "id": r.id,
                "region": r.name,
                "region_id": r.region_id,
            }
            for r in rows
        ]
    }


@sii_geo.get("/communes/{sii_region_id}")
def list_sii_communes(sii_region_id: int, db: Session = Depends(get_db)):
    """Comunas SII de una región. Shape compatible (id + commune)."""
    rows = (
        db.query(SiiCommuneModel)
        .filter(SiiCommuneModel.sii_region_id == sii_region_id)
        .order_by(SiiCommuneModel.name)
        .all()
    )
    return {
        "message": [
            {
                "id": c.id,
                "commune": c.name,
                "region_id": c.sii_region_id,
                "commune_id": c.commune_id,
            }
            for c in rows
        ]
    }
