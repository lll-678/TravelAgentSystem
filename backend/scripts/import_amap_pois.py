import argparse
import sys
from pathlib import Path

from sqlalchemy.orm import Session

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings
from app.db.init_db import create_all
from app.db.session import create_app_engine
from app.services.amap_import_service import import_amap_pois_to_db


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import real campus POIs from AMap Place Around Web Service.")
    parser.add_argument("--database-url", default=settings.dev_database_url)
    parser.add_argument("--center-lng", type=float, default=settings.osm_fallback_lng)
    parser.add_argument("--center-lat", type=float, default=settings.osm_fallback_lat)
    parser.add_argument("--radius", type=int, default=settings.osm_fallback_dist)
    parser.add_argument("--keyword", action="append", dest="keywords")
    parser.add_argument("--max-pages", type=int, default=3)
    parser.add_argument("--request-interval", type=float, default=0.3)
    parser.add_argument("--reset-facilities", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    engine = create_app_engine(args.database_url)
    create_all(engine)
    with Session(engine) as session:
        summary = import_amap_pois_to_db(
            session=session,
            api_key=settings.amap_web_api_key or "",
            center_lng=args.center_lng,
            center_lat=args.center_lat,
            radius=args.radius,
            keywords=args.keywords,
            max_pages=args.max_pages,
            reset_facilities=args.reset_facilities,
            request_interval=args.request_interval,
        )

    print("[amap-poi-import] database:", args.database_url)
    for key, value in summary.items():
        if key != "algorithm_trace":
            print(f"[amap-poi-import] {key}: {value}")


if __name__ == "__main__":
    main()
