# Real Estate Toolkit

Framework **normalizable** para monitorear avisos de compra/venta/alquiler de
propiedades en los portales inmobiliarios más importantes de Argentina, armar
un matching por tus propios criterios (zona/geolocalización, ambientes,
baños, m², antigüedad, amenities, exterior, servicios) y recibir por mail,
todos los días, sólo lo nuevo que matchea.

## Qué resuelve

1. **Escanea** varios portales con los mismos criterios de búsqueda
   (`config/config.yaml`), en dos "perfiles" independientes — típicamente
   Compra y Alquiler, cada uno con su propio rango de precio, moneda y
   destinatario.
2. **Normaliza** cada aviso a un mismo modelo (`Property`), sin importar de
   qué sitio vino.
3. **Puntúa** cada aviso de 0 a 100% según qué tan bien matchea tus
   criterios: zona, operación, tipo, precio, ambientes, dormitorios, baños
   (mínimo) y m2 son filtros duros — si no los cumple, se descarta, no se
   muestra con "70% de match". Dentro de esos filtros, m2 y baños todavía
   gradúan el score (cuanto más grande/más baños, mejor); zona y
   orientación suman más score cuanto más arriba está tu preferencia, sin
   excluir; parking suma si tiene, sin ser excluyente. Sólo se muestran los
   avisos con 50% o más (configurable).
4. **Convierte moneda** cuando hace falta: un alquiler publicado en USD se
   compara contra tu rango en ARS usando la cotización del día (o
   viceversa), en vez de descartarlo por estar en la moneda "equivocada".
5. **No repite**: guarda qué avisos ya viste (por perfil), así del segundo
   día en adelante el mail trae sólo lo nuevo.
6. **Manda un mail por perfil** diario a quien vos quieras (no hace falta
   que tenga Claude ni acceso a este repo) — corre solo, todos los días a
   las 17hs, vía GitHub Actions sobre un runner propio (tu computadora,
   registrada como self-hosted runner — varios portales bloquean las IPs
   de datacenter de la nube compartida de GitHub, no una IP residencial).
   Compra y alquiler nunca se mezclan en el mismo mail.

## ⚠️ Antes de usarlo

Mirar avisos públicos de propiedades es de mucho menor riesgo que
automatizar una postulación laboral (no hay login ni "aplicar" de por
medio), pero igual: respetá `robots.txt`, un rate limit razonable, y usá la
API oficial de un portal si la tiene en vez de scrapear su HTML — ver
`docs/PLATAFORMAS.md`. Los conectores incluidos son **plantillas de
ejemplo**: cada quien implementa la búsqueda real de los portales que le
interesen.

## Estructura del repo

```
config/
  config.example.yaml      # criterios de búsqueda + email destinatario
docs/
  ARQUITECTURA.md            # cómo encajan las piezas
  CONFIGURACION.md            # qué significa cada campo de config.yaml
  PLATAFORMAS.md                # notas por portal y qué tan bloqueado está cada uno
  DESPLIEGUE.md                  # cómo registrar tu compu como runner y dejarlo corriendo solo
  CONTRIBUIR.md                    # cómo sumar un portal nuevo
.github/workflows/
  daily-scan.yml                    # cron diario (17hs Argentina)
src/realestate/
  models.py                          # Property (el "idioma común")
  config.py                           # criterios de búsqueda tipados (compartidos + por perfil)
  fx.py                                 # cotización del dólar del día
  geo.py                                # distancia entre coordenadas
  matching.py                           # motor de scoring 0-100%
  storage.py                             # qué avisos ya viste, por perfil
  notifier.py                             # arma y manda el mail de un perfil
  connectors/                              # un módulo por portal
  cli.py                                     # scan / config-check
tests/
```

## Cómo normalizarlo a tu caso

1. Cloná el repo y creá un entorno virtual:
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -e ".[dev]"
   ```
2. Copiá `config/config.example.yaml` a `config/config.yaml`, completá tus
   zonas/rangos/amenities y el email de destino, y **commiteálo** (no tiene
   credenciales, sólo criterios de búsqueda).
3. Implementá o activá los conectores de los portales que te interesen
   (`src/realestate/connectors/`) — ver `docs/PLATAFORMAS.md`.
4. Corré los tests y probá en seco:
   ```bash
   pytest
   cp .env.example .env   # completá GMAIL_USER / GMAIL_APP_PASSWORD para probar local
   python -m realestate.cli scan --dry-run
   ```
5. Seguí `docs/DESPLIEGUE.md` para cargar los secrets en GitHub y dejarlo
   corriendo solo todos los días a las 17hs.

## Filosofía del proyecto

Vos definís qué es "una buena propiedad" en tu propio `config.yaml` — con
rangos, no valores exactos — y el sistema hace el trabajo repetitivo de
mirar varios sitios todos los días y avisarte sólo cuando aparece algo
nuevo que realmente matchea.

## Documentación

- [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md)
- [`docs/CONFIGURACION.md`](docs/CONFIGURACION.md)
- [`docs/PLATAFORMAS.md`](docs/PLATAFORMAS.md)
- [`docs/DESPLIEGUE.md`](docs/DESPLIEGUE.md)
- [`docs/CONTRIBUIR.md`](docs/CONTRIBUIR.md)

## Licencia

MIT — ver [LICENSE](LICENSE).
