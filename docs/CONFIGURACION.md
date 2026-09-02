# Configuración

## `config/config.yaml`

A diferencia de un `.env`, este archivo **sí se commitea** (no tiene
credenciales, sólo tus criterios de búsqueda) — el workflow de GitHub
Actions lo necesita presente en el repo para poder correr el scan diario sin
que nadie lo tenga que completar a mano cada vez.

| Sección | Campo | Descripción |
|---|---|---|
| `search` | `operation` | `"venta"` o `"alquiler"`. Filtro duro. |
| `search` | `property_types` | Lista de tipos aceptados (`departamento`, `casa`, `ph`, ...). Filtro duro; vacío = cualquiera. |
| `search` | `zones` | Nombres de barrio/comuna a matchear por texto. Vacío = sin filtro por nombre. |
| `search` | `geo_zones` | Lista de `{lat, lon, radius_km}`. Si el aviso trae coordenadas, tiene prioridad sobre `zones`. |
| `search` | `price` | `{min, max, tolerance}` — `tolerance` es cuánto te podés pasar del máximo antes de que se descarte el aviso. |
| `search` | `ambientes` / `dormitorios` / `banos` / `m2_cubiertos` / `antiguedad` | `{min, max, weight, tolerance}` — dentro del rango = 100% en ese campo; `tolerance` define qué tan rápido decae el score al alejarse del rango; `weight` pesa ese campo en el promedio final. |
| `search` | `amenities` / `exterior` / `servicios` | `{wanted: [...], weight}` — score = proporción de la lista deseada que el aviso cumple. |
| `search` | `min_score` | Puntaje mínimo (0-100) para que un aviso se muestre/mande. Por defecto 50. |
| — | `sources` | Conectores activos (deben existir en `src/realestate/connectors/`). |
| `email` | `recipient` | A quién se le manda el mail diario. |
| `email` | `sender_name` | Nombre que aparece como remitente. |

## Credenciales de email

Nunca van en `config.yaml`. Para correr localmente, copiá `.env.example` a
`.env` y completá `GMAIL_USER` / `GMAIL_APP_PASSWORD`. Para producción
(GitHub Actions), van como *Secrets* del repo — ver `docs/DESPLIEGUE.md`.
