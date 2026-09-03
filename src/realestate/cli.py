"""CLI del scan diario.

Uso:
    python -m realestate.cli scan
    python -m realestate.cli scan --dry-run
    python -m realestate.cli config-check

`scan` corre TODOS los perfiles configurados (ej: Compra y Alquiler), cada
uno contra todas las fuentes activas, y manda UN MAIL POR PERFIL (nunca
mezclados) — ver docs/ARQUITECTURA.md.
"""
from __future__ import annotations

import argparse
import importlib
from pathlib import Path

from .config import AppConfig, ProfileConfig, load_config
from .fx import get_ars_per_usd
from .matching import rank_properties
from .models import Property
from .notifier import send_email
from .storage import SeenStore

CONNECTOR_REGISTRY: dict[str, tuple[str, str]] = {
    "mercadolibre": ("realestate.connectors.mercadolibre", "MercadoLibreConnector"),
    "argenprop": ("realestate.connectors.argenprop", "ArgenpropConnector"),
    "zonaprop": ("realestate.connectors.zonaprop", "ZonapropConnector"),
    "remax": ("realestate.connectors.remax", "RemaxConnector"),
    "mudafy": ("realestate.connectors.mudafy", "MudafyConnector"),
    "cabaprop": ("realestate.connectors.cabaprop", "CabapropConnector"),
    "buscadorprop": ("realestate.connectors.buscadorprop", "BuscadorpropConnector"),
    "toribio_achaval": ("realestate.connectors.toribio_achaval", "ToribioAchavalConnector"),
    "inmuebles_clarin": ("realestate.connectors.inmuebles_clarin", "InmueblesClarinConnector"),
    "soloduenos": ("realestate.connectors.soloduenos", "SoloDuenosConnector"),
    "buscainmueble": ("realestate.connectors.buscainmueble", "BuscaInmuebleConnector"),
    "lepore": ("realestate.connectors.lepore", "LeporeConnector"),
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
    print(f"Zonas (orden de preferencia): {', '.join(config.shared.zones) or '(sin filtro por nombre)'}")
    print(f"Score mínimo: {config.shared.min_score}%")
    for profile in config.profiles:
        print(
            f"- Perfil '{profile.label}' ({profile.operation}): "
            f"precio {profile.price.min}-{profile.price.max}, "
            f"destinatario: {profile.recipient or '(sin configurar)'}"
        )


def _scan_profile(
    config: AppConfig, profile: ProfileConfig, seen_dir: Path, dry_run: bool, ars_per_usd: float
) -> None:
    criteria = config.criteria_for(profile, ars_per_usd=ars_per_usd)
    seen = SeenStore.load(seen_dir / f"seen_{profile.operation}.json")
    is_first_run = len(seen.seen_ids) == 0

    all_properties: list[Property] = []
    for source in config.sources:
        connector = _load_connector(source)
        try:
            all_properties.extend(connector.search_listings(criteria))
        except NotImplementedError as exc:
            print(f"[{profile.label}] [{source}] sin implementar todavía: {exc}")
        except Exception as exc:  # un conector roto no debe tumbar la corrida entera
            print(f"[{profile.label}] [{source}] ERROR durante la búsqueda, se lo salta: {exc!r}")

    ranked = rank_properties(all_properties, criteria)

    to_send = [
        r for r in ranked
        if is_first_run or seen.is_new(f"{r.property.source}:{r.property.id}")
    ]

    for r in ranked:
        seen.mark_seen(f"{r.property.source}:{r.property.id}")
    seen.save()

    print(
        f"[{profile.label}] {len(ranked)} propiedades matchean "
        f"(score >= {criteria.min_score}%). {len(to_send)} son nuevas."
    )

    if dry_run:
        print(f"[{profile.label}] (--dry-run) No se mandó el mail.")
    else:
        send_email(to_send, is_first_run, profile, config.sender_name, config.smtp_user, config.smtp_password)


def cmd_debug_source(args: argparse.Namespace) -> None:
    """Trae avisos crudos de UNA fuente y muestra cómo quedaron normalizados
    — para verificar o ajustar el mapeo de campos de un conector contra
    datos reales, sin arriesgar mandar ningún mail."""
    config = load_config(args.config, args.env)
    profile = next((p for p in config.profiles if p.operation == args.operation), None)
    if profile is None:
        raise SystemExit(f"No hay ningún perfil con operation='{args.operation}' en config.yaml.")

    criteria = config.criteria_for(profile)
    connector = _load_connector(args.source)
    properties = connector.search_listings(criteria)

    print(f"{len(properties)} avisos encontrados en '{args.source}' (antes de aplicar el matching).")
    for prop in properties[: args.limit]:
        print("-" * 60)
        print(f"id={prop.id!r}  operation={prop.operation!r}  property_type={prop.property_type!r}")
        print(f"price={prop.price} {prop.currency}  neighborhood={prop.neighborhood!r}")
        print(f"ambientes={prop.ambientes}  dormitorios={prop.dormitorios}  banos={prop.banos}")
        print(f"m2_cubiertos={prop.m2_cubiertos}  m2_totales={prop.m2_totales}  parking={prop.parking}")
        print(f"exterior={prop.exterior}  orientacion={prop.orientacion!r}  apto_credito={prop.apto_credito}")
        print(f"url={prop.url}")
        if args.raw_keys and isinstance(prop.raw, dict):
            print(f"raw_keys={sorted(prop.raw.keys())}")


def cmd_fetch_url(args: argparse.Namespace) -> None:
    """Trae el HTML/JS crudo de una URL puntual — para inspeccionar la
    estructura real de un sitio (o un bundle de JS minificado, que suele
    venir en una sola línea gigante) antes de escribir su conector.
    `--grep` busca la palabra en TODO el texto (no línea por línea) y
    muestra un fragmento de contexto alrededor de cada ocurrencia."""
    import requests

    from .probe import REQUEST_HEADERS

    response = requests.get(args.url, headers=REQUEST_HEADERS, timeout=20)
    print(f"status={response.status_code} length={len(response.content)}")
    text = response.text
    if args.grep:
        target = args.grep.lower()
        text_lower = text.lower()
        positions = []
        cursor = 0
        while len(positions) < args.limit:
            idx = text_lower.find(target, cursor)
            if idx == -1:
                break
            positions.append(idx)
            cursor = idx + len(target)
        print(f"{len(positions)} ocurrencias de '{args.grep}' (mostrando hasta {args.limit}):")
        for pos in positions:
            snippet = text[max(0, pos - 80) : pos + len(args.grep) + 250].replace("\n", " ")
            print(f"...{snippet}...")
    else:
        print(text[args.start : args.start + args.length])


def cmd_probe_sites(args: argparse.Namespace) -> None:
    """GET simple a la home de cada sitio configurado como fuente, para ver
    quién bloquea el tráfico ANTES de escribir un parser completo."""
    from .probe import probe_all

    for result in probe_all():
        print(result)


def cmd_scan(args: argparse.Namespace) -> None:
    config = load_config(args.config, args.env)
    seen_dir = Path(args.seen_dir)
    # Una sola consulta de cotización por corrida (no una por perfil), para
    # no golpear la API de más y para que compra/alquiler usen el mismo
    # valor del día si ambos la necesitaran.
    ars_per_usd = get_ars_per_usd(fallback=config.fx_fallback_ars_per_usd)
    print(f"Cotización del día usada para comparar precios: {ars_per_usd:.0f} ARS/USD")
    for profile in config.profiles:
        _scan_profile(config, profile, seen_dir, args.dry_run, ars_per_usd)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="realestate")
    sub = parser.add_subparsers(dest="command", required=True)

    scan_parser = sub.add_parser("scan", help="Escanea todos los perfiles y fuentes, y manda un mail por perfil")
    scan_parser.add_argument("--config", default="config/config.yaml")
    scan_parser.add_argument("--env", default=".env")
    scan_parser.add_argument("--seen-dir", default="data")
    scan_parser.add_argument(
        "--dry-run", action="store_true", help="No envía los mails, sólo muestra el resultado"
    )
    scan_parser.set_defaults(func=cmd_scan)

    config_parser = sub.add_parser("config-check", help="Valida config.yaml y .env")
    config_parser.add_argument("--config", default="config/config.yaml")
    config_parser.add_argument("--env", default=".env")
    config_parser.set_defaults(func=cmd_config_check)

    debug_parser = sub.add_parser(
        "debug-source",
        help="Trae avisos crudos de una fuente y muestra cómo se normalizaron (no manda mail)",
    )
    debug_parser.add_argument("source")
    debug_parser.add_argument("--config", default="config/config.yaml")
    debug_parser.add_argument("--env", default=".env")
    debug_parser.add_argument("--operation", default="venta")
    debug_parser.add_argument("--limit", type=int, default=3)
    debug_parser.add_argument(
        "--raw-keys", action="store_true", help="Mostrar también las claves del dato crudo (raw) de cada aviso"
    )
    debug_parser.set_defaults(func=cmd_debug_source)

    probe_parser = sub.add_parser(
        "probe-sites",
        help="GET simple a la home de cada sitio, para ver cuáles bloquean el tráfico (no manda mail)",
    )
    probe_parser.set_defaults(func=cmd_probe_sites)

    fetch_parser = sub.add_parser(
        "fetch-url",
        help="Trae el HTML crudo de una URL puntual, para inspeccionar un sitio antes de escribir su conector",
    )
    fetch_parser.add_argument("url")
    fetch_parser.add_argument("--grep", default="", help="Sólo mostrar líneas que contengan este texto")
    fetch_parser.add_argument("--limit", type=int, default=40, help="Máximo de líneas a mostrar con --grep")
    fetch_parser.add_argument("--start", type=int, default=0, help="Offset de caracteres (sin --grep)")
    fetch_parser.add_argument("--length", type=int, default=3000, help="Cantidad de caracteres (sin --grep)")
    fetch_parser.set_defaults(func=cmd_fetch_url)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
