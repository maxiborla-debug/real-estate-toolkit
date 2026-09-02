"""CLI del scan diario.

Uso:
    python -m realestate.cli scan
    python -m realestate.cli scan --dry-run
    python -m realestate.cli config-check
"""
from __future__ import annotations

import argparse
import importlib

from .config import load_config
from .matching import rank_properties
from .models import Property
from .notifier import send_email
from .storage import SeenStore

CONNECTOR_REGISTRY: dict[str, tuple[str, str]] = {
    "zonaprop": ("realestate.connectors.zonaprop", "ZonapropConnector"),
    "argenprop": ("realestate.connectors.argenprop", "ArgenpropConnector"),
    "mercadolibre": ("realestate.connectors.mercadolibre", "MercadoLibreConnector"),
    "properati": ("realestate.connectors.properati", "ProperatiConnector"),
}


def _load_connector(name: str):
    if name not in CONNECTOR_REGISTRY:
        raise ValueError(f"Fuente desconocida: '{name}'. Agregala a CONNECTOR_REGISTRY en cli.py.")
    module_path, class_name = CONNECTOR_REGISTRY[name]
    module = importlib.import_module(module_path)
    return getattr(module, class_name)()


def cmd_config_check(args: argparse.Namespace) -> None:
    config = load_config(args.config, args.env)
    print(f"Fuentes configuradas: {', '.join(config.sources) or '(ninguna)'}")
    print(f"Operación: {config.search.operation}")
    print(f"Zonas por nombre: {', '.join(config.search.zones) or '(sin filtro por nombre)'}")
    print(f"Zonas geolocalizadas: {len(config.search.geo_zones)}")
    print(f"Score mínimo: {config.search.min_score}%")
    print(f"Email destino: {config.email.recipient or '(sin configurar)'}")


def cmd_scan(args: argparse.Namespace) -> None:
    config = load_config(args.config, args.env)
    seen = SeenStore.load(args.seen)
    is_first_run = len(seen.seen_ids) == 0

    all_properties: list[Property] = []
    for source in config.sources:
        connector = _load_connector(source)
        try:
            all_properties.extend(connector.search_listings(config.search))
        except NotImplementedError as exc:
            print(f"[{source}] sin implementar todavía: {exc}")

    ranked = rank_properties(all_properties, config.search)

    to_send = [
        r for r in ranked
        if is_first_run or seen.is_new(f"{r.property.source}:{r.property.id}")
    ]

    for r in ranked:
        seen.mark_seen(f"{r.property.source}:{r.property.id}")
    seen.save()

    print(f"{len(ranked)} propiedades matchean (score >= {config.search.min_score}%).")
    print(f"{len(to_send)} son nuevas y se van a mandar por mail.")

    if args.dry_run:
        print("(--dry-run) No se mandó el mail.")
    else:
        send_email(to_send, is_first_run, config.email, config.smtp_user, config.smtp_password)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="realestate")
    sub = parser.add_subparsers(dest="command", required=True)

    scan_parser = sub.add_parser("scan", help="Escanea todas las fuentes configuradas y manda el mail")
    scan_parser.add_argument("--config", default="config/config.yaml")
    scan_parser.add_argument("--env", default=".env")
    scan_parser.add_argument("--seen", default="data/seen.json")
    scan_parser.add_argument(
        "--dry-run", action="store_true", help="No envía el mail, sólo muestra el resultado"
    )
    scan_parser.set_defaults(func=cmd_scan)

    config_parser = sub.add_parser("config-check", help="Valida config.yaml y .env")
    config_parser.add_argument("--config", default="config/config.yaml")
    config_parser.add_argument("--env", default=".env")
    config_parser.set_defaults(func=cmd_config_check)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
