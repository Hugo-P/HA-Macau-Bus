import hashlib
from datetime import datetime
import urllib.request
import ssl
import json
import logging

from .const import API_BASE, API_UA, API_HUID

_LOGGER = logging.getLogger(__name__)

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE


def make_token(param_str):
    h = hashlib.md5(param_str.encode("utf-8")).hexdigest()
    t = datetime.now().strftime("%Y%m%d%H%M")
    a = list(h)
    a.insert(24, t[8]); a.insert(25, t[9]); a.insert(26, t[10]); a.insert(27, t[11])
    a.insert(12, t[4]); a.insert(13, t[5]); a.insert(14, t[6]); a.insert(15, t[7])
    a.insert(4, t[0]); a.insert(5, t[1]); a.insert(6, t[2]); a.insert(7, t[3])
    return "".join(a)


def api_get(path, param_str):
    token = make_token(param_str)
    url = f"{API_BASE}{path}?{param_str}"
    req = urllib.request.Request(url, headers={
        "token": token, "User-Agent": API_UA, "Accept": "application/json",
        "Referer": f"{API_BASE}/macauweb/", "Origin": API_BASE,
    })
    resp = urllib.request.urlopen(req, context=SSL_CTX, timeout=10)
    return json.loads(resp.read().decode("utf-8"))


def api_post_form(path, param_str):
    token = make_token(param_str)
    url = f"{API_BASE}{path}"
    req = urllib.request.Request(url, data=param_str.encode("utf-8"), headers={
        "token": token, "User-Agent": API_UA,
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "Referer": f"{API_BASE}/macauweb/", "Origin": API_BASE,
    }, method="POST")
    resp = urllib.request.urlopen(req, context=SSL_CTX, timeout=10)
    return json.loads(resp.read().decode("utf-8"))


def build_dashboard(lat, lon, radius=500, route_filter=None):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    stops_resp = api_get("/ddbus/common/station/gps",
                         f"log={lon}&lat={lat}&range={radius}&device=web&HUID={API_HUID}&needStaInfo=true&lang=zh-tw")
    nearby = stops_resp.get("data", [])
    if not nearby:
        return {"error": "附近沒有站點", "timestamp": now}

    nearby_codes = {s["stationCode"] for s in nearby}
    nearby_coords = {s["stationCode"]: (float(s["latitude"]), float(s["longitude"])) for s in nearby}

    routes_resp = api_post_form("/macauweb/getRouteAndCompanyList.html", "lang=zh-tw&device=web")
    route_list = routes_resp.get("data", {}).get("routeList", [])
    if route_filter:
        route_filter = [r.strip().upper() for r in route_filter.split(",") if r.strip()]
        route_list = [r for r in route_list if r.get("routeName", "").upper() in route_filter]

    results = []
    for route in route_list:
        rn = route.get("routeName", "")
        dr = route.get("direction", "0")
        color = route.get("color", "")
        try:
            bus_resp = api_post_form("/macauweb/routestation/bus",
                                     f"routeName={rn}&dir={dr}&lang=zh-tw&device=web")
        except Exception:
            continue
        if bus_resp.get("header") not in ("000", {"status": "000"}):
            continue
        route_info = bus_resp.get("data", {}).get("routeInfo", [])
        if not route_info:
            continue

        user_stop_idx = None
        best_dist = float('inf')
        for idx, station in enumerate(route_info):
            code = station.get("staCode")
            if code in nearby_codes:
                dlat = (nearby_coords[code][0] - float(lat)) * 111320
                dlon = (nearby_coords[code][1] - float(lon)) * 111320
                dist = (dlat * dlat + dlon * dlon) ** 0.5
                if dist < best_dist:
                    best_dist = dist
                    user_stop_idx = idx

        if user_stop_idx is None:
            continue

        nearby_stop_name = ""
        if user_stop_idx is not None:
            sta = route_info[user_stop_idx]
            nearby_stop_name = sta.get("staName", sta.get("staCode", ""))

        try:
            rd_resp = api_post_form("/macauweb/getRouteData.html",
                                    f"action=sd&routeName={rn}&dir={dr}&lang=zh-tw&device=web")
            rd_info = rd_resp.get("data", {}).get("routeInfo", [])
            dest_name = rd_info[-1].get("staName", "-") if rd_info and isinstance(rd_info, list) else "-"
        except Exception:
            dest_name = "-"

        bus_stops = []
        for idx, station in enumerate(route_info):
            sta_code = station.get("staCode", "")
            for bus in station.get("busInfo", []):
                sc = bus.get("stopCount", "")
                bus_status = bus.get("status", "")
                if sc == "0":
                    status = "到站"
                elif sc == "x":
                    status = "即將到達"
                elif sc == "f":
                    status = "即將開出"
                elif sc == "":
                    status = "-"
                else:
                    status = f"{sc}站"

                remaining = None
                if user_stop_idx is not None:
                    remaining = user_stop_idx - idx
                if remaining is not None and remaining < 0:
                    continue
                if remaining == 0 and bus_status == "0":
                    continue

                bus_stops.append({
                    "stationCode": sta_code,
                    "busPlate": bus.get("busPlate", ""),
                    "stopCount": sc,
                    "status": status,
                    "stationIndex": idx,
                    "remainingStops": remaining,
                })

        bus_stops.sort(key=lambda x: (
            x["remainingStops"] is None,
            x["remainingStops"] is not None and x["remainingStops"] < 0,
            x["remainingStops"] if x["remainingStops"] is not None and x["remainingStops"] >= 0 else 9999
        ))

        results.append({
            "routeName": rn,
            "destination": dest_name,
            "nearbyStop": nearby_stop_name,
            "color": color,
            "stationCount": len(route_info),
            "nearbyCount": sum(1 for s in route_info if s.get("staCode") in nearby_codes),
            "userStopIndex": user_stop_idx,
            "buses": bus_stops,
        })

    return {
        "nearbyStops": nearby,
        "routes": results,
        "totalRoutes": len(route_list),
        "checkedRoutes": len(results),
        "timestamp": now,
    }
