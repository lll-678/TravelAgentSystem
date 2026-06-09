import argparse
import sys
from collections import Counter
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings
from app.db.session import create_app_engine
from app.models import Destination, Facility
from app.services.map_data_service import get_map_stats_from_db
from app.services.search_service import search_places_from_db


SCENES = {
    "bupt_shahe": ("campus", "北京邮电大学沙河校区"),
    "summer_palace": ("scenic", "北京颐和园"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check course data-volume requirements.")
    parser.add_argument("--database-url", default=settings.dev_database_url)
    parser.add_argument("--min-destinations", type=int, default=200)
    parser.add_argument("--min-buildings", type=int, default=20)
    parser.add_argument("--min-facilities", type=int, default=50)
    parser.add_argument("--min-facility-categories", type=int, default=10)
    parser.add_argument("--min-roads", type=int, default=200)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    engine = create_app_engine(args.database_url)
    failures: list[str] = []
    with Session(engine) as session:
        destinations = len(session.scalars(select(Destination)).all())
        print(f"[data-check] destinations={destinations}")
        if destinations < args.min_destinations:
            failures.append(f"destinations {destinations} < {args.min_destinations}")

        for scene_key, (scope, label) in SCENES.items():
            stats = get_map_stats_from_db(session, scene_key=scene_key)
            places = search_places_from_db(session, "", None, 1000, scope=scope, scene_key=scene_key)["items"]
            categories = _facility_category_counts(session, scene_key)
            print(
                f"[data-check] {scene_key} {label}: roads={stats['roads']} buildings={stats['buildings']} "
                f"facilities={stats['facilities']} facility_categories={len(categories)} selectable_places={len(places)}"
            )
            if stats["roads"] < args.min_roads:
                failures.append(f"{scene_key}.roads {stats['roads']} < {args.min_roads}")
            if stats["buildings"] < args.min_buildings:
                failures.append(f"{scene_key}.buildings {stats['buildings']} < {args.min_buildings}")
            if stats["facilities"] < args.min_facilities:
                failures.append(f"{scene_key}.facilities {stats['facilities']} < {args.min_facilities}")
            if len(categories) < args.min_facility_categories:
                failures.append(
                    f"{scene_key}.facility_categories {len(categories)} < {args.min_facility_categories}"
                )

    if failures:
        for failure in failures:
            print(f"[data-check] FAIL {failure}")
        raise SystemExit(1)
    print("[data-check] OK")


def _facility_category_counts(session: Session, scene_key: str) -> Counter[str]:
    counter: Counter[str] = Counter()
    for facility in session.scalars(select(Facility).where(Facility.scene_key == scene_key)).all():
        counter[facility.category.code if facility.category else "unknown"] += 1
    return counter


if __name__ == "__main__":
    main()
