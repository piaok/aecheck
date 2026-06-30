import json
import os
import threading
import time
from typing import List, Optional, Dict, Any
from datetime import date, datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DATA_FILE = os.path.join(DATA_DIR, "standards.json")

_lock = threading.Lock()
_last_mtime: float = 0.0
_cached_data: List[Dict[str, Any]] = []

def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def _load_all() -> List[Dict[str, Any]]:
    global _last_mtime, _cached_data
    _ensure_data_dir()
    if not os.path.exists(DATA_FILE):
        _cached_data = []
        return _cached_data
    try:
        mtime = os.path.getmtime(DATA_FILE)
    except OSError:
        return _cached_data
    if mtime == _last_mtime and _cached_data is not None:
        return _cached_data
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            _cached_data = data
            _last_mtime = mtime
        else:
            data = _cached_data
    except (json.JSONDecodeError, OSError):
        data = _cached_data
    return data

def _save_all(data: List[Dict[str, Any]]):
    global _last_mtime, _cached_data
    _ensure_data_dir()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    _cached_data = data
    try:
        _last_mtime = os.path.getmtime(DATA_FILE)
    except OSError:
        pass

def _next_id(data: List[Dict[str, Any]]) -> int:
    if not data:
        return 1
    return max(item.get("id", 0) for item in data) + 1

class StandardDB:
    """JSON-based standards storage with mtime-based cache."""

    def __init__(self):
        self._data = _load_all()

    def count(self) -> int:
        with _lock:
            self._data = _load_all()
            return len(self._data)

    def get_all(self, keyword: Optional[str] = None, skip: int = 0, limit: int = 20) -> tuple:
        with _lock:
            self._data = _load_all()
            items = self._data
            if keyword:
                kw = keyword.lower()
                items = [
                    s for s in items
                    if kw in s.get("standard_number", "").lower()
                    or kw in s.get("standard_name", "").lower()
                ]
            total = len(items)
            items = items[skip : skip + limit]
            return total, items

    def get_by_id(self, standard_id: int) -> Optional[Dict[str, Any]]:
        with _lock:
            self._data = _load_all()
            for s in self._data:
                if s.get("id") == standard_id:
                    return s
        return None

    def get_by_number(self, standard_number: str) -> Optional[Dict[str, Any]]:
        with _lock:
            self._data = _load_all()
            clean = standard_number.replace(" ", "").upper()
            for s in self._data:
                if s.get("standard_number", "").replace(" ", "").upper() == clean:
                    return s
        return None

    def search_by_number_prefix(self, prefix: str, limit: int = 10) -> List[Dict[str, Any]]:
        with _lock:
            self._data = _load_all()
            clean = prefix.replace(" ", "").upper()[:8]
            return [
                s for s in self._data
                if clean in s.get("standard_number", "").replace(" ", "").upper()
            ][:limit]

    def create(self, standard_number: str, standard_name: str, status: str = "现行",
               release_date: Optional[str] = None, implement_date: Optional[str] = None,
               abolish_date: Optional[str] = None, replace_by: Optional[str] = None,
               source: Optional[str] = None) -> Dict[str, Any]:
        with _lock:
            self._data = _load_all()
            new_id = _next_id(self._data)
            now = datetime.now().strftime("%Y-%m-%d")
            item = {
                "id": new_id,
                "standard_number": standard_number,
                "standard_name": standard_name,
                "status": status,
                "release_date": release_date if release_date else None,
                "implement_date": implement_date if implement_date else None,
                "abolish_date": abolish_date if abolish_date else None,
                "replace_by": replace_by if replace_by else None,
                "source": source,
                "created_at": now,
                "updated_at": now,
            }
            self._data.append(item)
            _save_all(self._data)
            return item

    def update(self, standard_id: int, **kwargs) -> Optional[Dict[str, Any]]:
        with _lock:
            self._data = _load_all()
            for s in self._data:
                if s.get("id") == standard_id:
                    for key, value in kwargs.items():
                        if key in ("standard_number", "standard_name", "status",
                                   "release_date", "implement_date", "abolish_date",
                                   "replace_by", "source"):
                            s[key] = value if value else None
                    s["updated_at"] = datetime.now().strftime("%Y-%m-%d")
                    _save_all(self._data)
                    return s
        return None

    def delete(self, standard_id: int) -> bool:
        with _lock:
            self._data = _load_all()
            for i, s in enumerate(self._data):
                if s.get("id") == standard_id:
                    self._data.pop(i)
                    _save_all(self._data)
                    return True
        return False

    def find_exact_match(self, standard_number: str) -> Optional[Dict[str, Any]]:
        with _lock:
            self._data = _load_all()
            clean = standard_number.replace(" ", "").upper()
            for s in self._data:
                if s.get("standard_number", "").replace(" ", "").upper() == clean:
                    return s
        return None

db = StandardDB()

def init_db():
    """Ensure data file exists and has content."""
    _ensure_data_dir()
    if not os.path.exists(DATA_FILE):
        from init_data import INITIAL_DATA
        now = datetime.now().strftime("%Y-%m-%d")
        data = []
        for i, item in enumerate(INITIAL_DATA, 1):
            item["id"] = i
            item["created_at"] = ""
            item["updated_at"] = ""
            data.append(item)
        _save_all(data)
    else:
        existing = _load_all()
        if not existing:
            from init_data import INITIAL_DATA
            now = datetime.now().strftime("%Y-%m-%d")
            data = []
            for i, item in enumerate(INITIAL_DATA, 1):
                item["id"] = i
                item["created_at"] = ""
                item["updated_at"] = ""
                data.append(item)
            _save_all(data)
