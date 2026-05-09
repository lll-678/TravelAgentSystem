"""Route Service - 处理路线规划相关的业务逻辑"""

from sqlalchemy.orm import Session

from app.core.graph import Graph
from app.db import crud


class RouteService:
    """处理路线规划、距离计算等"""

    def __init__(self, graph: Graph):
        self.graph = graph

    def find_shortest_path(self, db: Session, start_poi_id: int, end_poi_id: int) -> dict | None:
        """查找最短路径"""
        start_poi = crud.get_poi_by_id(db, start_poi_id)
        end_poi = crud.get_poi_by_id(db, end_poi_id)

        if not start_poi or not end_poi:
            return None

        # 如果图中没有边（仅有节点），则基于经纬度构建完全图（每对节点之间的距离）
        def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
            from math import radians, sin, cos, sqrt, asin

            # 返回公里数
            dlat = radians(lat2 - lat1)
            dlon = radians(lon2 - lon1)
            a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
            c = 2 * asin(sqrt(a))
            R = 6371.0
            return R * c

        # if graph has no nodes loaded (app started before DB init), load nodes from DB
        if not self.graph.nodes:
            pois = crud.get_all_pois(db, skip=0, limit=10000)
            for poi in pois:
                self.graph.add_node(
                    str(poi.id),
                    {
                        "name": poi.name,
                        "type": poi.type,
                        "latitude": poi.latitude,
                        "longitude": poi.longitude,
                        "floor": poi.floor,
                    },
                )

        # build edges if adjacency lists are empty
        any_edges = any(len(edges) > 0 for edges in self.graph.adjacency_list.values())
        if not any_edges:
            # build complete graph using node coordinates where available
            nodes = list(self.graph.nodes.items())
            for nid, node in nodes:
                lat1 = node.data.get("latitude") if node.data else None
                lon1 = node.data.get("longitude") if node.data else None
                if lat1 is None or lon1 is None:
                    continue
                for mid, mnode in nodes:
                    if nid == mid:
                        continue
                    lat2 = mnode.data.get("latitude") if mnode.data else None
                    lon2 = mnode.data.get("longitude") if mnode.data else None
                    if lat2 is None or lon2 is None:
                        continue
                    dist = haversine(lat1, lon1, lat2, lon2)
                    # add bidirectional edges
                    self.graph.add_edge(nid, mid, dist)

        path_node_ids = self.graph.dijkstra(str(start_poi_id), str(end_poi_id))

        # compute total distance along the path
        total_distance_km = 0.0
        path_coords: list[dict] = []
        if path_node_ids:
            for pid in path_node_ids:
                node = self.graph.nodes.get(pid)
                if node and node.data:
                    path_coords.append(
                        {
                            "id": int(pid),
                            "name": node.data.get("name"),
                            "latitude": node.data.get("latitude"),
                            "longitude": node.data.get("longitude"),
                        }
                    )

            # sum consecutive distances from adjacency list (if available)
            for a, b in zip(path_node_ids, path_node_ids[1:]):
                found = False
                for neigh, w in self.graph.adjacency_list.get(a, []):
                    if neigh == b:
                        total_distance_km += w
                        found = True
                        break
                if not found:
                    # fallback to haversine using stored coordinates
                    na = self.graph.nodes.get(a)
                    nb = self.graph.nodes.get(b)
                    if na and nb and na.data and nb.data:
                        total_distance_km += haversine(
                            na.data.get("latitude"),
                            na.data.get("longitude"),
                            nb.data.get("latitude"),
                            nb.data.get("longitude"),
                        )

        # estimate time (default assume driving 40 km/h)
        avg_speed_kmh = 40.0
        estimated_hours = total_distance_km / avg_speed_kmh if avg_speed_kmh > 0 else 0

        return {
            "start_poi": {
                "id": start_poi.id,
                "name": start_poi.name,
                "latitude": start_poi.latitude,
                "longitude": start_poi.longitude,
            },
            "end_poi": {
                "id": end_poi.id,
                "name": end_poi.name,
                "latitude": end_poi.latitude,
                "longitude": end_poi.longitude,
            },
            "path_nodes": path_coords,
            "distance": round(total_distance_km, 4),
            "estimated_time_hours": round(estimated_hours, 3),
        }

    def add_edge(self, from_poi_id: int, to_poi_id: int, distance: float) -> None:
        """在图中添加边（连接两个景点）"""
        self.graph.add_edge(str(from_poi_id), str(to_poi_id), distance)

    def get_nearby_pois(self, db: Session, poi_id: int, radius_km: float = 1.0) -> list[dict]:
        """获取距离某个 POI 指定范围内的景点（后续可使用地理坐标计算）"""
        # 这是占位实现，后续需要基于坐标计算距离
        return []
