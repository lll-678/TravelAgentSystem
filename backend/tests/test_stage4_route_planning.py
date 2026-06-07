from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.algorithms.route_planning import (
    GraphEdge,
    build_bidirectional_graph,
    dijkstra_shortest_path,
)
from app.api.v1.routes import RoutePlanRequest, plan_route
from app.db.init_db import create_all
from app.seed.sample_data import BUPT_SHAHE_CENTER
from app.seed.seed_all import seed_demo_data
from app.services.route_service import plan_route_from_db


def test_dijkstra_prefers_shorter_weighted_path() -> None:
    edges = [
        GraphEdge(id=1, from_node_id=1, to_node_id=2, distance=10, duration=10, geometry=[]),
        GraphEdge(id=2, from_node_id=2, to_node_id=3, distance=10, duration=10, geometry=[]),
        GraphEdge(id=3, from_node_id=1, to_node_id=3, distance=50, duration=50, geometry=[]),
    ]

    result = dijkstra_shortest_path(build_bidirectional_graph(edges), 1, 3, weight="distance")

    assert result.node_ids == [1, 2, 3]
    assert result.graph_distance == 20
    assert [edge.id for edge in result.edges] == [1, 2]


def test_route_service_returns_seeded_graph_path() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        seed_demo_data(session)
        route = plan_route_from_db(
            session,
            {
                "start_lng": BUPT_SHAHE_CENTER[0],
                "start_lat": BUPT_SHAHE_CENTER[1],
                "end_lng": BUPT_SHAHE_CENTER[0] + 0.0015,
                "end_lat": BUPT_SHAHE_CENTER[1] + 0.0012,
                "strategy": "shortest_distance",
                "mode": "walk",
            },
        )

    assert route["algorithm_trace"]["stage"] == "stage-4-db-graph"
    assert route["algorithm_trace"]["algorithm"] == "Dijkstra shortest path"
    assert route["distance"] > 0
    assert route["duration"] > 0
    assert len(route["path"]) >= 3
    assert len(route["node_ids"]) >= 2
    assert route["steps"][0]["text"].startswith("起点吸附到道路节点")


def test_route_api_handler_uses_seeded_database() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        seed_demo_data(session)
        route = plan_route(RoutePlanRequest(), session)

    assert route["strategy"] == "shortest_distance"
    assert route["mode"] == "walk"
    assert route["algorithm_trace"]["topology_source"] == "map_nodes/map_edges seeded database"
    assert route["distance"] > 0
    assert route["path"][0] == [116.28333, 40.15608]
