BUPT_SHAHE_CAMPUS_BOUNDS = {
    "min_lng": 116.2770,
    "max_lng": 116.2896,
    "min_lat": 40.1534,
    "max_lat": 40.1602,
}


def is_in_bupt_shahe_bounds(lng: float, lat: float) -> bool:
    return (
        BUPT_SHAHE_CAMPUS_BOUNDS["min_lng"] <= lng <= BUPT_SHAHE_CAMPUS_BOUNDS["max_lng"]
        and BUPT_SHAHE_CAMPUS_BOUNDS["min_lat"] <= lat <= BUPT_SHAHE_CAMPUS_BOUNDS["max_lat"]
    )
