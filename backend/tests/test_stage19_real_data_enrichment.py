from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.algorithms.coordinates import gcj02_to_wgs84, wgs84_to_gcj02
from app.db.init_db import create_all
from app.models import Facility, FacilityCategory, MapNode
from app.services import amap_import_service
from app.services.amap_import_service import (
    classify_amap_poi,
    fetch_amap_pois,
    import_amap_poi_items_to_db,
)


def test_coordinate_conversion_round_trips_beijing_point() -> None:
    lng, lat = 116.28333, 40.15608

    gcj_lng, gcj_lat = wgs84_to_gcj02(lng, lat)
    restored_lng, restored_lat = gcj02_to_wgs84(gcj_lng, gcj_lat)

    assert abs(gcj_lng - lng) > 0.001
    assert abs(gcj_lat - lat) > 0.001
    assert abs(restored_lng - lng) < 0.00002
    assert abs(restored_lat - lat) < 0.00002


def test_import_amap_poi_items_converts_coordinates_and_deduplicates() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    center_lng, center_lat = 116.28333, 40.15608
    poi_lng, poi_lat = 116.28380, 40.15620
    poi_gcj_lng, poi_gcj_lat = wgs84_to_gcj02(poi_lng, poi_lat)
    pois = [
        {
            "id": "B0TEST001",
            "name": "北京邮电大学沙河校区生活超市",
            "type": "购物服务;便民商店/便利店;便民商店/便利店",
            "typecode": "060200",
            "address": "沙河校区",
            "location": f"{poi_gcj_lng},{poi_gcj_lat}",
            "_query_keyword": "超市",
        },
        {
            "id": "B0TEST001",
            "name": "北京邮电大学沙河校区生活超市",
            "type": "购物服务;便民商店/便利店;便民商店/便利店",
            "location": f"{poi_gcj_lng},{poi_gcj_lat}",
            "_query_keyword": "便利店",
        },
    ]

    with Session(engine) as session:
        session.add(MapNode(external_id="node-1", name="center", lng=center_lng, lat=center_lat))
        session.flush()
        summary = import_amap_poi_items_to_db(
            session=session,
            pois=pois,
            center_lng=center_lng,
            center_lat=center_lat,
            radius=500,
            reset_facilities=True,
        )
        facilities = session.scalars(select(Facility)).all()
        categories = session.scalars(select(FacilityCategory)).all()
        category_code = facilities[0].category.code

    assert summary["source"] == "amap-place-around"
    assert summary["raw_pois"] == 2
    assert summary["facilities_imported"] == 1
    assert summary["facilities_skipped"] == 1
    assert len(facilities) == 1
    assert category_code == "shop"
    assert facilities[0].nearest_node_id is not None
    assert abs(facilities[0].lng - poi_lng) < 0.00002
    assert abs(facilities[0].lat - poi_lat) < 0.00002
    assert any(category.code == "service" for category in categories)


def test_fetch_amap_pois_uses_place_around_without_exposing_key(monkeypatch) -> None:
    calls = []

    def fake_get(url, params, timeout):
        calls.append({"url": url, "params": params, "timeout": timeout})
        return FakeResponse(
            {
                "status": "1",
                "count": "1",
                "pois": [
                    {
                        "id": "B0TEST002",
                        "name": "北京邮电大学沙河校区公共厕所",
                        "type": "公共设施;公共厕所;公共厕所",
                        "location": "116.289408,40.157331",
                    }
                ],
            }
        )

    monkeypatch.setattr(amap_import_service.httpx, "get", fake_get)

    pois, trace = fetch_amap_pois(
        api_key="secret-key",
        center_lng=116.28333,
        center_lat=40.15608,
        radius=300,
        keywords=["厕所"],
        max_pages=1,
    )

    assert len(pois) == 1
    assert calls[0]["url"] == amap_import_service.AMAP_PLACE_AROUND_ENDPOINT
    assert calls[0]["params"]["key"] == "secret-key"
    assert calls[0]["params"]["location"] == "116.289408,40.157331"
    assert trace["requests"] == 1
    assert "secret-key" not in str(trace)


def test_fetch_amap_pois_retries_qps_limit(monkeypatch) -> None:
    calls = []
    sleeps = []

    def fake_get(url, params, timeout):
        calls.append({"url": url, "params": params, "timeout": timeout})
        if len(calls) == 1:
            return FakeResponse(
                {
                    "status": "0",
                    "info": "CUQPS_HAS_EXCEEDED_THE_LIMIT",
                    "infocode": "10021",
                }
            )
        return FakeResponse(
            {
                "status": "1",
                "count": "0",
                "pois": [],
            }
        )

    monkeypatch.setattr(amap_import_service.httpx, "get", fake_get)
    monkeypatch.setattr(amap_import_service.time, "sleep", lambda seconds: sleeps.append(seconds))

    pois, trace = fetch_amap_pois(
        api_key="secret-key",
        center_lng=116.28333,
        center_lat=40.15608,
        radius=300,
        keywords=["厕所"],
        max_pages=1,
        request_interval=0,
    )

    assert pois == []
    assert trace["requests"] == 1
    assert len(calls) == 2
    assert sleeps == [0.3]


def test_classify_amap_poi_covers_common_campus_facilities() -> None:
    assert classify_amap_poi({"name": "校医院", "type": "医疗保健服务"}) == "clinic"
    assert classify_amap_poi({"name": "篮球场", "type": "体育休闲服务"}) == "sport"
    assert classify_amap_poi({"name": "南区食堂", "type": "餐饮服务"}) == "canteen"


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self.payload
