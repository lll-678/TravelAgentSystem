import time
from typing import Any

import httpx
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.algorithms.coordinates import gcj02_to_wgs84, wgs84_to_gcj02
from app.algorithms.route_planning import approximate_distance_meters
from app.models import Facility, FacilityCategory, MapNode
from app.seed.sample_data import BUPT_SHAHE_CENTER, FACILITY_CATEGORIES


class AMapPoiImportError(RuntimeError):
    pass


AMAP_PLACE_AROUND_ENDPOINT = "https://restapi.amap.com/v3/place/around"
AMAP_DEFAULT_KEYWORDS = [
    "厕所",
    "卫生间",
    "饮水",
    "便利店",
    "超市",
    "快递",
    "食堂",
    "餐厅",
    "咖啡",
    "校门",
    "图书馆",
    "体育",
    "篮球场",
    "医院",
    "医务室",
    "公交",
    "地铁",
    "停车",
    "ATM",
    "银行",
]
AMAP_OFFSET = 25


def fetch_amap_pois(
    api_key: str,
    center_lng: float = BUPT_SHAHE_CENTER[0],
    center_lat: float = BUPT_SHAHE_CENTER[1],
    radius: int = 1500,
    keywords: list[str] | None = None,
    max_pages: int = 3,
    request_interval: float = 0.3,
    timeout: float = 10.0,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not api_key:
        raise AMapPoiImportError("AMAP_WEB_API_KEY is not configured for backend POI import.")
    if radius <= 0:
        raise AMapPoiImportError("AMap POI radius must be positive.")
    if max_pages <= 0:
        raise AMapPoiImportError("AMap POI max_pages must be positive.")

    query_lng, query_lat = wgs84_to_gcj02(center_lng, center_lat)
    query_keywords = keywords or AMAP_DEFAULT_KEYWORDS
    collected: list[dict[str, Any]] = []
    request_count = 0

    for keyword in query_keywords:
        for page in range(1, max_pages + 1):
            request_count += 1
            payload = _request_amap_page(
                api_key=api_key,
                location=f"{query_lng},{query_lat}",
                radius=radius,
                keyword=keyword,
                page=page,
                timeout=timeout,
                retries=3,
                retry_interval=max(request_interval, 0.3),
            )
            pois = payload.get("pois") or []
            for poi in pois:
                if isinstance(poi, dict):
                    poi["_query_keyword"] = keyword
                    collected.append(poi)
            if request_interval > 0:
                time.sleep(request_interval)
            if len(pois) < AMAP_OFFSET:
                break

    trace = {
        "endpoint": AMAP_PLACE_AROUND_ENDPOINT,
        "center_wgs84": [center_lng, center_lat],
        "center_gcj02": [query_lng, query_lat],
        "radius": radius,
        "keywords": len(query_keywords),
        "requests": request_count,
        "raw_pois": len(collected),
    }
    return collected, trace


def import_amap_pois_to_db(
    session: Session,
    api_key: str,
    center_lng: float = BUPT_SHAHE_CENTER[0],
    center_lat: float = BUPT_SHAHE_CENTER[1],
    radius: int = 1500,
    keywords: list[str] | None = None,
    max_pages: int = 3,
    reset_facilities: bool = False,
    request_interval: float = 0.3,
) -> dict[str, Any]:
    pois, fetch_trace = fetch_amap_pois(
        api_key=api_key,
        center_lng=center_lng,
        center_lat=center_lat,
        radius=radius,
        keywords=keywords,
        max_pages=max_pages,
        request_interval=request_interval,
    )
    return import_amap_poi_items_to_db(
        session=session,
        pois=pois,
        center_lng=center_lng,
        center_lat=center_lat,
        radius=radius,
        reset_facilities=reset_facilities,
        fetch_trace=fetch_trace,
    )


def import_amap_poi_items_to_db(
    session: Session,
    pois: list[dict[str, Any]],
    center_lng: float = BUPT_SHAHE_CENTER[0],
    center_lat: float = BUPT_SHAHE_CENTER[1],
    radius: int = 1500,
    reset_facilities: bool = False,
    fetch_trace: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if reset_facilities:
        session.execute(delete(Facility))
        session.execute(delete(FacilityCategory))
        session.flush()

    categories = _load_or_create_standard_categories(session)
    nodes = list(session.scalars(select(MapNode).order_by(MapNode.id)).all())
    existing_signatures = {
        _facility_signature(facility.name, facility.lng, facility.lat)
        for facility in session.scalars(select(Facility)).all()
    }
    seen_amap_ids: set[str] = set()
    imported = 0
    skipped = 0

    for poi in pois:
        normalized = _normalize_amap_poi(poi)
        if normalized is None:
            skipped += 1
            continue
        if normalized["amap_id"] and normalized["amap_id"] in seen_amap_ids:
            skipped += 1
            continue
        seen_amap_ids.add(normalized["amap_id"])

        distance = approximate_distance_meters(
            (center_lng, center_lat),
            (normalized["lng"], normalized["lat"]),
        )
        if distance > radius + 100:
            skipped += 1
            continue

        signature = _facility_signature(normalized["name"], normalized["lng"], normalized["lat"])
        if signature in existing_signatures:
            skipped += 1
            continue

        category_code = classify_amap_poi(normalized)
        category = categories[category_code]
        nearest_node = _nearest_node(normalized["lng"], normalized["lat"], nodes)
        session.add(
            Facility(
                name=normalized["name"],
                category_id=category.id,
                nearest_node_id=nearest_node.id if nearest_node else None,
                lng=normalized["lng"],
                lat=normalized["lat"],
                description=_build_description(normalized),
            )
        )
        existing_signatures.add(signature)
        imported += 1

    session.commit()
    return {
        "source": "amap-place-around",
        "center": [center_lng, center_lat],
        "radius": radius,
        "raw_pois": len(pois),
        "facilities_imported": imported,
        "facilities_skipped": skipped,
        "reset_facilities": reset_facilities,
        "algorithm_trace": {
            "stage": "stage-19-real-data-enrichment",
            "pipeline": "AMap Place Around POI -> GCJ-02 to WGS84 -> category classify -> nearest graph node -> facilities",
            "routing_topology": "unchanged; OSM/seed map_nodes and map_edges remain the route graph",
            "dedup": "AMap id plus normalized name and rounded coordinate",
            "fetch": fetch_trace or {},
        },
    }


def classify_amap_poi(poi: dict[str, Any]) -> str:
    text = f"{poi.get('name', '')} {poi.get('type', '')} {poi.get('address', '')} {poi.get('query_keyword', '')}"
    text = text.casefold()
    rules = [
        ("toilet", ["厕所", "卫生间", "洗手间", "公共厕所"]),
        ("water", ["饮水", "直饮水", "饮水机", "开水"]),
        ("shop", ["便利店", "超市", "商店", "快递", "驿站", "文具", "购物"]),
        ("canteen", ["食堂", "餐厅", "饭店", "餐饮", "咖啡", "小吃", "快餐"]),
        ("gate", ["校门", "大门", "入口", "门岗"]),
        ("library", ["图书馆", "阅览", "借阅"]),
        ("sport", ["体育", "运动", "篮球", "足球", "操场", "健身"]),
        ("clinic", ["医院", "医务", "诊所", "药房", "急救"]),
        ("transport", ["公交", "地铁", "停车", "车站", "校车", "单车", "交通"]),
        ("atm", ["atm", "银行", "自动取款"]),
    ]
    for category, tokens in rules:
        if any(token in text for token in tokens):
            return category
    return "service"


def _request_amap_page(
    api_key: str,
    location: str,
    radius: int,
    keyword: str,
    page: int,
    timeout: float,
    retries: int,
    retry_interval: float,
) -> dict[str, Any]:
    for attempt in range(retries + 1):
        response = httpx.get(
            AMAP_PLACE_AROUND_ENDPOINT,
            params={
                "key": api_key,
                "location": location,
                "radius": radius,
                "keywords": keyword,
                "offset": AMAP_OFFSET,
                "page": page,
                "extensions": "all",
                "sortrule": "distance",
                "output": "json",
            },
            timeout=timeout,
        )
        response.raise_for_status()
        payload = response.json()
        if str(payload.get("status")) == "1":
            return payload
        info = payload.get("info") or "unknown error"
        infocode = payload.get("infocode") or "unknown"
        if str(infocode) == "10021" and attempt < retries:
            time.sleep(retry_interval * (attempt + 1))
            continue
        raise AMapPoiImportError(f"AMap POI request failed: {info} ({infocode}).")
    raise AMapPoiImportError("AMap POI request failed after retries.")


def _normalize_amap_poi(poi: dict[str, Any]) -> dict[str, Any] | None:
    name = str(poi.get("name") or "").strip()
    location = str(poi.get("location") or "").strip()
    if not name or "," not in location:
        return None
    try:
        gcj_lng, gcj_lat = [float(item) for item in location.split(",", maxsplit=1)]
    except ValueError:
        return None
    lng, lat = gcj02_to_wgs84(gcj_lng, gcj_lat)
    return {
        "amap_id": str(poi.get("id") or ""),
        "name": name,
        "lng": lng,
        "lat": lat,
        "gcj_lng": gcj_lng,
        "gcj_lat": gcj_lat,
        "type": str(poi.get("type") or ""),
        "typecode": str(poi.get("typecode") or ""),
        "address": _stringify_address(poi.get("address")),
        "query_keyword": str(poi.get("_query_keyword") or ""),
    }


def _stringify_address(value: Any) -> str:
    if isinstance(value, list):
        return " ".join(str(item) for item in value if item)
    return str(value or "")


def _build_description(poi: dict[str, Any]) -> str:
    parts = [
        "Imported from AMap Web Service.",
        f"source=amap",
        f"amap_id={poi['amap_id']}",
        f"type={poi['type']}",
        f"typecode={poi['typecode']}",
        f"address={poi['address']}",
    ]
    return "; ".join(part for part in parts if part and not part.endswith("="))


def _load_or_create_standard_categories(session: Session) -> dict[str, FacilityCategory]:
    categories = {
        category.code: category
        for category in session.scalars(select(FacilityCategory)).all()
    }
    for code, name in [*FACILITY_CATEGORIES, ("service", "公共服务")]:
        if code in categories:
            continue
        category = FacilityCategory(code=code, name=name)
        session.add(category)
        categories[code] = category
    session.flush()
    return categories


def _nearest_node(lng: float, lat: float, nodes: list[MapNode]) -> MapNode | None:
    if not nodes:
        return None
    return min(
        nodes,
        key=lambda node: approximate_distance_meters((lng, lat), (node.lng, node.lat)),
    )


def _facility_signature(name: str, lng: float, lat: float) -> tuple[str, float, float]:
    return " ".join(name.casefold().split()), round(lng, 4), round(lat, 4)
