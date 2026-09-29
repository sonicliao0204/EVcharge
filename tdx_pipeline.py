import os
import requests
import json
import sqlite3
from datetime import datetime

class TDXIngestion:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = self._get_token()

    def _get_token(self) -> str:
        url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        res = requests.post(url, data=data, timeout=10)
        res.raise_for_status()
        return res.json().get("access_token")

    def fetch_raw_data(self):
        headers = {"authorization": f"Bearer {self.token}"}
        static_url = "https://tdx.transportdata.tw/api/basic/v2/Road/Traffic/ChargingStation/EV/Static?$format=JSON"
        static_res = requests.get(static_url, headers=headers, timeout=20)
        static_res.raise_for_status()

        dynamic_url = "https://tdx.transportdata.tw/api/basic/v2/Road/Traffic/ChargingStation/EV/Dynamic?$format=JSON"
        dynamic_res = requests.get(dynamic_url, headers=headers, timeout=20)
        dynamic_res.raise_for_status()

        return static_res.json(), dynamic_res.json()

class EVDataProcessor:
    CPO_MAPPING = {
        "遠傳": "FET", "遠傳電信": "FET",
        "源捷": "U-POWER", "旭電馳": "U-POWER", "u-power": "U-POWER",
        "華城": "EVALUE", "華城電能": "EVALUE", "evalue": "EVALUE",
        "特爾": "TAIL", "特爾電力": "TAIL", "tail": "TAIL",
        "中興電工": "iCharging", "icharging": "iCharging",
        "裕電": "YES", "裕電俥電": "YES"
    }

    @classmethod
    def normalize_cpo(cls, raw_cpo: str) -> str:
        if not raw_cpo: return "OTHER"
        for key, std_name in cls.CPO_MAPPING.items():
            if key in raw_cpo.lower(): return std_name
        return raw_cpo.strip()

    @classmethod
    def process_and_deduplicate(cls, static_raw: list, dynamic_raw: list) -> list:
        live_status_map = {}
        for d in dynamic_raw:
            s_id = d.get("StationID")
            statuses = [c.get("Status") for c in d.get("EVConnectorLiveStatus", []) if c.get("Status")]
            if "Charging" in statuses: agg_status = "Charging"
            elif "Available" in statuses: agg_status = "Available"
            elif "Faulted" in statuses: agg_status = "Faulted"
            else: agg_status = "Offline"
            live_status_map[s_id] = agg_status

        seen_stations = set()
        clean_dataset = []

        for st in static_raw:
            station_id = st.get("StationID")
            pos = st.get("StationPosition", {})
            lat, lon = pos.get("PositionLat"), pos.get("PositionLon")
            if not station_id or not lat or not lon or station_id in seen_stations:
                continue

            raw_cpo = st.get("OperatorName", {}).get("Zh_tw", "")
            total_kw = sum(eq.get("EquipmentPower", 0) or 0 for eq in st.get("ChargingEquipments", []))
            total_plugs = sum(eq.get("ConnectorCount", 0) or 0 for eq in st.get("ChargingEquipments", []))

            clean_dataset.append({
                "station_id": station_id,
                "name": st.get("StationName", {}).get("Zh_tw", "未命名站點"),
                "cpo": cls.normalize_cpo(raw_cpo),
                "lat": round(float(lat), 6),
                "lng": round(float(lon), 6),
                "total_kw": total_kw,
                "total_plugs": total_plugs,
                "live_status": live_status_map.get(station_id, "Offline"),
                "updated_at": datetime.now().isoformat()
            })
            seen_stations.add(station_id)

        return clean_dataset

class EVDatabaseMart:
    def __init__(self, db_path="data/evcharge.db"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS stations (
                    station_id TEXT PRIMARY KEY, name TEXT, cpo TEXT, lat REAL, lng REAL, 
                    total_kw REAL, total_plugs INTEGER, live_status TEXT, updated_at TEXT)
            """)

    def save(self, dataset: list):
        with self.conn:
            self.conn.executemany("""
                INSERT OR REPLACE INTO stations 
                VALUES (:station_id, :name, :cpo, :lat, :lng, :total_kw, :total_plugs, :live_status, :updated_at)
            """, dataset)

    def export_marts(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT station_id, name, cpo, lat, lng, total_kw, total_plugs, live_status FROM stations")
        map_data = [
            {"id": r[0], "name": r[1], "cpo": r[2], "lat": r[3], "lng": r[4], "total_kw": r[5], "total_plugs": r[6], "live_status": r[7]}
            for r in cursor.fetchall()
        ]
        with open("data/stations_live.json", "w", encoding="utf-8") as f:
            json.dump(map_data, f, ensure_ascii=False, indent=2)
