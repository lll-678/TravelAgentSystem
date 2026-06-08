from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.algorithms.ranking import top_k_smallest
from app.api.v1.facilities import nearby_facilities
from app.db.init_db import create_all
from app.models import Facility
from app.seed.sample_data import BUPT_SHAHE_CENTER
from app.seed.seed_all import seed_demo_data
from app.services.facility_service import get_nearby_facilities_from_db


def test_top_k_smallest_uses_heap_ordering() -> None:
    items = [{"name": "far", "distance": 30}, {"name": "near", "distance": 5}, {"name": "mid", "distance": 12}]

    result = top_k_smallest(items, key=lambda item: item["distance"], k=2)

    assert [item["name"] for item in result] == ["near", "mid"]


def test_nearby_facilities_are_ranked_by_graph_distance() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        seed_demo_data(session)
        payload = get_nearby_facilities_from_db(
            session=session,
            current_lng=BUPT_SHAHE_CENTER[0],
            current_lat=BUPT_SHAHE_CENTER[1],
            category="water",
            radius=5000,
            limit=3,
        )

    distances = [item["distance"] for item in payload["items"]]
    assert payload["algorithm_trace"]["stage"] == "stage-5-facility-graph-distance"
    assert payload["algorithm_trace"]["ranking"] == "Top-K heap by graph distance"
    assert len(payload["items"]) == 3
    assert distances == sorted(distances)
    assert all(item["category"] == "water" for item in payload["items"])
    assert all(len(item["routePath"]) >= 2 for item in payload["items"])


def test_nearby_facilities_api_handler_uses_seeded_database() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        seed_demo_data(session)
        payload = nearby_facilities(
            origin_place_id=None,
            current_lng=BUPT_SHAHE_CENTER[0],
            current_lat=BUPT_SHAHE_CENTER[1],
            category=None,
            radius=5000,
            limit=5,
            db=session,
        )

    assert payload["total"] >= 5
    assert len(payload["items"]) == 5
    assert payload["items"][0]["distance"] <= payload["items"][-1]["distance"]
    assert payload["algorithm_trace"]["distance"] == "Dijkstra graph distance plus snap distance"


def test_nearby_facilities_accepts_origin_place_id() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        seed_demo_data(session)
        origin = session.query(Facility).order_by(Facility.id).first()
        assert origin is not None
        origin_id = origin.id
        origin_name = origin.name
        payload = get_nearby_facilities_from_db(
            session=session,
            origin_place_id=f"facility-{origin_id}",
            current_lng=0,
            current_lat=0,
            category="water",
            radius=5000,
            limit=3,
        )

    assert payload["origin"]["id"] == f"facility-{origin_id}"
    assert payload["origin"]["source"] == "facility"
    assert payload["origin"]["name"] == origin_name
    assert payload["algorithm_trace"]["origin_resolution"] == "origin_place_id"
    assert payload["algorithm_trace"]["origin_id"] == f"facility-{origin_id}"
    assert len(payload["items"]) == 3


def test_nearby_facilities_accepts_category_name_query() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        seed_demo_data(session)
        payload = get_nearby_facilities_from_db(
            session=session,
            current_lng=BUPT_SHAHE_CENTER[0],
            current_lat=BUPT_SHAHE_CENTER[1],
            category="厕所",
            radius=5000,
            limit=3,
        )

    assert payload["category"] == "toilet"
    assert payload["algorithm_trace"]["resolved_category"] == "toilet"
    assert len(payload["items"]) == 3
    assert all(item["category"] == "toilet" for item in payload["items"])
