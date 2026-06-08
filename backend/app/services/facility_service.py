from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.algorithms.ranking import top_k_smallest
from app.algorithms.route_planning import (
    GraphEdge,
    GraphNode,
    RouteNotFoundError,
    approximate_distance_meters,
    build_bidirectional_graph,
    dijkstra_shortest_path,
    find_nearest_node,
)
from app.models import Facility, FacilityCategory, MapEdge, MapNode
from app.services.route_service import build_path_coordinates


def get_nearby_facilities_from_db(
    session: Session,
    current_lng: float,
    current_lat: float,
    category: str | None,
    radius: int,
    limit: int,
) -> dict[str, Any]:
    nodes, edges = _load_graph_data(session)
    if not edges:
        raise RouteNotFoundError("No map edges are available.")

    start = (current_lng, current_lat)
    start_snap = find_nearest_node(current_lng, current_lat, nodes)
    nodes_by_id = {node.id: node for node in nodes}
    graph = build_bidirectional_graph(edges)

    resolved_category = _resolve_category_code(session, category)
    candidates = _load_facilities(session, resolved_category)
    enriched = []
    for facility in candidates:
        facility_node = _resolve_facility_node(facility, nodes, nodes_by_id)
        facility_point = (facility.lng, facility.lat)
        try:
            route = dijkstra_shortest_path(graph, start_snap.node.id, facility_node.id)
        except RouteNotFoundError:
            continue

        facility_snap_distance = approximate_distance_meters(
            facility_point,
            (facility_node.lng, facility_node.lat),
        )
        distance = start_snap.distance + route.graph_distance + facility_snap_distance
        if distance > radius:
            continue

        enriched.append(
            {
                "id": f"facility-{facility.id}",
                "name": facility.name,
                "category": facility.category.code,
                "category_name": facility.category.name,
                "lng": facility.lng,
                "lat": facility.lat,
                "description": facility.description,
                "nearest_node_id": facility_node.id,
                "distance": round(distance),
                "duration": round(route.graph_duration + (start_snap.distance + facility_snap_distance) / 1.2),
                "routePath": build_path_coordinates(start, facility_point, start_snap.node, facility_node, route.edges),
                "node_ids": route.node_ids,
            }
        )

    ranked = top_k_smallest(enriched, key=lambda item: float(item["distance"]), k=limit)
    return {
        "items": ranked,
        "total": len(enriched),
        "category": resolved_category,
        "category_query": category,
        "radius": radius,
        "algorithm_trace": {
            "stage": "stage-5-facility-graph-distance",
            "filter": "facility category before routing",
            "category_lookup": "code/name/contains matching",
            "resolved_category": resolved_category or "",
            "distance": "Dijkstra graph distance plus snap distance",
            "ranking": "Top-K heap by graph distance",
            "candidates": str(len(candidates)),
            "returned": str(len(ranked)),
            "nodes": str(len(nodes)),
            "edges": str(len(edges)),
        },
    }


def _load_graph_data(session: Session) -> tuple[list[GraphNode], list[GraphEdge]]:
    nodes = [
        GraphNode(
            id=node.id,
            lng=node.lng,
            lat=node.lat,
            name=node.name,
        )
        for node in session.scalars(select(MapNode).order_by(MapNode.id)).all()
    ]
    edges = [
        GraphEdge(
            id=edge.id,
            from_node_id=edge.from_node_id,
            to_node_id=edge.to_node_id,
            distance=edge.distance,
            duration=edge.walk_time,
            geometry=edge.geometry,
        )
        for edge in session.scalars(select(MapEdge).order_by(MapEdge.id)).all()
    ]
    return nodes, edges


def _load_facilities(session: Session, category: str | None) -> list[Facility]:
    query = select(Facility).options(selectinload(Facility.category)).order_by(Facility.id)
    if category:
        query = query.join(FacilityCategory).where(FacilityCategory.code == category)
    return list(session.scalars(query).all())


def _resolve_category_code(session: Session, category: str | None) -> str | None:
    if not category:
        return None
    keyword = category.strip().casefold()
    if not keyword:
        return None
    aliases = {
        "卫生间": "toilet",
        "厕所": "toilet",
        "洗手间": "toilet",
        "水": "water",
        "饮水": "water",
        "食堂": "canteen",
        "餐厅": "canteen",
        "超市": "shop",
        "商店": "shop",
        "便利店": "shop",
        "校门": "gate",
        "门": "gate",
        "图书馆": "library",
        "运动": "sport",
        "体育": "sport",
        "医院": "clinic",
        "医务": "clinic",
        "交通": "transport",
        "车站": "transport",
        "atm": "atm",
    }
    if keyword in aliases:
        return aliases[keyword]
    categories = session.scalars(select(FacilityCategory).order_by(FacilityCategory.id)).all()
    for item in categories:
        if keyword in {item.code.casefold(), item.name.casefold()}:
            return item.code
    for item in categories:
        haystack = f"{item.code} {item.name}".casefold()
        if keyword in haystack or haystack in keyword:
            return item.code
    return category


def _resolve_facility_node(
    facility: Facility,
    nodes: list[GraphNode],
    nodes_by_id: dict[int, GraphNode],
) -> GraphNode:
    if facility.nearest_node_id and facility.nearest_node_id in nodes_by_id:
        return nodes_by_id[facility.nearest_node_id]
    return find_nearest_node(facility.lng, facility.lat, nodes).node
