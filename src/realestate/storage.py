"""Registro persistente de qué avisos ya vimos, para mandar sólo los nuevos
a partir del segundo día.

Se guarda como JSON en el repo (`data/seen.json`): el workflow de GitHub
Actions lo commitea de vuelta después de cada corrida. Ver
docs/DESPLIEGUE.md.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class SeenStore:
    path: Path
    seen_ids: set[str] = field(default_factory=set)

    @classmethod
    def load(cls, path: str | Path = "data/seen.json") -> "SeenStore":
        path = Path(path)
        if not path.exists():
            return cls(path=path, seen_ids=set())
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(path=path, seen_ids=set(data.get("seen_ids", [])))

    def is_new(self, listing_id: str) -> bool:
        return listing_id not in self.seen_ids

    def mark_seen(self, listing_id: str) -> None:
        self.seen_ids.add(listing_id)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "seen_ids": sorted(self.seen_ids),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self.path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
