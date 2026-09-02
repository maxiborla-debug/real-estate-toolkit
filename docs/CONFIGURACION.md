# Configuración

## `config/config.yaml`

A diferencia de un `.env`, este archivo **sí se commitea** (no tiene
credenciales, sólo tus criterios de búsqueda) — el workflow de GitHub
Actions lo necesita presente en el repo para poder correr el scan diario
sin que nadie lo tenga que completar a mano cada vez.

### Nivel raíz

| Campo | Descripción |
|---|---|
| `sources` | Conectores activos (deben existir en `src/realestate/connectors/`). |
| `sender_name` | Nombre que aparece como remitente en todos los mails. |
| `fx_fallback_ars_per_usd` | Cotización de respaldo si falla la consulta del dólar del día (ver `fx.py`). |

### `shared` — se aplica igual a todos los perfiles

| Campo | Descripción |
|---|---|
| `property_types` | Tipos aceptados (`departamento`, `casa`, `ph`, `duplex`, `semipiso`, ...). Filtro duro; vacío = cualquiera. |
| `zones` | Barrios de más a menos preferido. Filtro duro (fuera de la lista se descarta) **y** gradúa el score: el primero de la lista puntúa más que el último. |
| `zone_weight` | Peso de esa graduación por barrio en el promedio final. |
| `geo_zones` | Lista de `{lat, lon, radius_km}`. Si el aviso trae coordenadas, tiene prioridad sobre `zones` para el filtro (pero no gradúa por preferencia). |
| `ambientes`, `dormitorios` | `{min, max, hard: true}` — fuera del rango se descarta. Dentro del rango, todos los valores puntúan igual. |
| `banos` | `{min, hard: true, bigger_is_better: true, soft_ceiling}` — exige un piso (ej: al menos 1), y por encima de ese piso, más baños suma más score hasta `soft_ceiling` (a partir de ahí ya es "el máximo"). |
| `m2` | `{min, max, hard: true, bigger_is_better: true}` — descarta fuera de rango; dentro del rango, más grande puntúa más. |
| `exterior_required` | `{wanted: [...], min_area_m2}` — al menos uno de la lista, sino se descarta. Si además informan el m2 de ese espacio, tiene que cumplir `min_area_m2` (si no lo informan, se deja pasar). |
| `orientacion` | `{tiers: [[...], [...], ...], weight}` — niveles de preferencia (el primer nivel es el mejor). No excluye, sólo suma score. |
| `parking_weight` | Peso del bonus por tener cochera. `0` para ignorarlo del todo. No es excluyente: sin dato, no penaliza. |
| `min_score` | Puntaje mínimo (0-100) para que un aviso se muestre/mande. |

### `profiles` — una entrada por operación (Compra, Alquiler, ...)

| Campo | Descripción |
|---|---|
| `operation` | `"venta"` o `"alquiler"`. |
| `label` | Nombre para el asunto del mail (ej: "Compra"). |
| `recipient` | A quién se le manda el mail de ESTE perfil. |
| `currency` | Moneda del rango de precio de este perfil (`"USD"`, `"ARS"`). |
| `price` | `{min, max, hard: true}`. Un aviso publicado en la otra moneda (ARS↔USD) se convierte con la cotización del día antes de comparar — no se descarta sólo por estar en otra moneda. |
| `apto_credito_required` | Sólo tiene sentido en `"venta"`. Si es `true`, descarta cualquier aviso que no declare explícitamente "apto crédito" (incluidos los que no lo aclaran). |

Cada perfil se escanea y se manda por mail **por separado** — nunca se
mezclan avisos de compra y alquiler en el mismo mail, y cada uno lleva su
propio registro de "ya visto" (`data/seen_venta.json`,
`data/seen_alquiler.json`).

## Credenciales de email

Nunca van en `config.yaml`. Para correr localmente, copiá `.env.example` a
`.env` y completá `GMAIL_USER` / `GMAIL_APP_PASSWORD`. Para producción
(GitHub Actions), van como *Secrets* del repo — ver `docs/DESPLIEGUE.md`.
