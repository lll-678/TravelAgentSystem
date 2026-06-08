from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.api.v1.indoor import IndoorRouteRequest, list_indoor_buildings, list_indoor_nodes, plan_indoor_route
from app.db.init_db import create_all
from app.models import IndoorEdge, IndoorNode
from app.seed.seed_all import seed_demo_data
from app.services.indoor_service import plan_indoor_route_from_db


SCIENCE_MUSEUM = "中国科学技术馆主展厅"


def test_seed_contains_indoor_building_graph() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        counts = seed_demo_data(session)
        nodes = session.scalars(select(IndoorNode).order_by(IndoorNode.id)).all()
        edges = session.scalars(select(IndoorEdge).order_by(IndoorEdge.id)).all()

    assert counts["indoor_nodes"] >= 76
    assert counts["indoor_edges"] >= 94
    assert any(node.node_type == "entrance" for node in nodes)
    assert any(node.node_type == "elevator" and node.floor == 3 for node in nodes)
    assert any(edge.access_type == "elevator" for edge in edges)


def test_indoor_route_crosses_floors_with_elevator() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        seed_demo_data(session)
        route = plan_indoor_route_from_db(
            session,
            {
                "building_name": "综合教学楼",
                "start_name": "一层大门",
                "end_name": "305 教室",
            },
        )

    assert route["algorithm_trace"]["stage"] == "stage-15-indoor-navigation"
    assert route["distance"] > 0
    assert route["duration"] > 0
    assert route["path"][0]["name"] == "一层大门"
    assert route["path"][-1]["name"] == "305 教室"
    assert any(step["access_type"] == "elevator" for step in route["steps"])
    assert route["path"][-1]["floor"] == 3


def test_indoor_api_handlers_use_seeded_database() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        seed_demo_data(session)
        buildings = list_indoor_buildings(session)
        nodes = list_indoor_nodes("综合教学楼", session)
        route = plan_indoor_route(IndoorRouteRequest(), session)

    assert buildings["total"] >= 2
    building_names = {building["building_name"] for building in buildings["items"]}
    assert {"综合教学楼", SCIENCE_MUSEUM}.issubset(building_names)
    teaching_building = next(building for building in buildings["items"] if building["building_name"] == "综合教学楼")
    assert teaching_building["floors"] == [1, 2, 3]
    assert nodes["total"] >= 19
    assert route["end"]["name"] == "305 教室"


def test_science_museum_indoor_graph_scale_and_floor_labels() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        seed_demo_data(session)
        nodes = list_indoor_nodes(SCIENCE_MUSEUM, session)
        science_node_ids = [
            node.id
            for node in session.scalars(
                select(IndoorNode).where(IndoorNode.building_name == SCIENCE_MUSEUM).order_by(IndoorNode.id)
            ).all()
        ]
        science_edge_count = len(
            session.scalars(
                select(IndoorEdge).where(IndoorEdge.building_name == SCIENCE_MUSEUM).order_by(IndoorEdge.id)
            ).all()
        )

    assert nodes["total"] >= 57
    assert science_edge_count >= 74
    assert science_node_ids
    assert {node["floor_label"] for node in nodes["items"]} == {"B1", "1F", "2F", "3F", "4F", "5F"}
    assert any(node["name"] == "西门入口" for node in nodes["items"])
    assert any(node["name"] == "4F 挑战与未来 C 厅" for node in nodes["items"])


def test_science_museum_accessible_route_uses_elevator_only_for_vertical_move() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        seed_demo_data(session)
        route = plan_indoor_route_from_db(
            session,
            {
                "building_name": SCIENCE_MUSEUM,
                "start_name": "西门入口",
                "end_name": "4F 挑战与未来 C 厅",
                "route_mode": "accessible",
            },
        )

    assert route["algorithm_trace"]["stage"] == "stage-38-indoor-navigation"
    assert route["algorithm_trace"]["route_mode"] == "accessible"
    assert route["algorithm_trace"]["vertical_traffic"] == "elevator"
    assert route["path"][0]["name"] == "西门入口"
    assert route["path"][-1]["name"] == "4F 挑战与未来 C 厅"
    assert route["path"][-1]["floor"] == 4
    assert any(node["name"] == "一层电梯厅" for node in route["path"])
    assert any(step["access_type"] == "elevator" for step in route["steps"])
    assert not any(step["access_type"] in {"stairs", "escalator"} for step in route["steps"])
    assert not any("楼梯间" in node["name"] or "扶梯" in node["name"] for node in route["path"])


def test_science_museum_same_floor_service_route_works() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        seed_demo_data(session)
        route = plan_indoor_route_from_db(
            session,
            {
                "building_name": SCIENCE_MUSEUM,
                "start_name": "一层大厅",
                "end_name": "一层文创商店",
                "route_mode": "normal",
            },
        )

    assert route["path"][0]["name"] == "一层大厅"
    assert route["path"][-1]["name"] == "一层文创商店"
    assert {node["floor"] for node in route["path"]} == {1}
