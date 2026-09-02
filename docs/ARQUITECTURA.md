# Arquitectura

## Flujo general (una corrida del cron diario)

```
Config (config.yaml + secrets de email)
        │
        ▼
Por cada fuente activa: Connector.search_listings(criteria) ──► [Property, ...]
        │
        ▼
matching.rank_properties(properties, criteria)
        │   - filtros duros: operación, tipo, zona (nombre o geolocalización), precio
        │   - criterios blandos ponderados: ambientes, dormitorios, baños, m2,
        │     antigüedad (rangos con tolerancia) + amenities/exterior/servicios (listas)
        ▼
Propiedades con score >= min_score (50% por defecto), ordenadas de mayor a menor
        │
        ▼
SeenStore: separa cuáles son nuevas (primera corrida = todas) vs ya vistas
        │
        ▼
notifier.send_email(nuevas) ──► un solo mail con todos los matches nuevos del día
        │
        ▼
SeenStore.save() ──► data/seen.json se commitea de vuelta al repo (workflow)
```

## Piezas

- **`models.py`**: `Property`, el modelo normalizado de un aviso, sin
  importar el portal de origen.
- **`config.py`**: `SearchCriteria` con dos tipos de criterio reutilizables
  — `RangeCriterion` (mín/máx/peso/tolerancia, para ambientes, baños, m2,
  antigüedad, precio) y `ListCriterion` (lista deseada + peso, para
  amenities/exterior/servicios).
- **`geo.py`**: distancia entre coordenadas (haversine), para el matching
  por círculos geográficos.
- **`matching.py`**: el corazón del sistema — `score_property` calcula
  0-100% por aviso; `rank_properties` filtra por `min_score` y ordena.
- **`storage.py`**: `SeenStore`, un registro JSON de IDs ya vistos, para que
  a partir del segundo día sólo se manden novedades.
- **`notifier.py`**: arma y manda el email (HTML) vía SMTP de Gmail.
- **`connectors/`**: un módulo por portal, misma interfaz
  (`RealEstateConnector`).
- **`cli.py`**: `scan` (corrida completa) y `config-check` (valida
  configuración sin scrapear nada).

## Por qué zona/operación/precio son "filtros duros" y el resto no

No tiene sentido mostrar un 70% de match para un depto que está en venta
cuando buscás alquilar, o a 40 km de la zona pedida — eso se descarta
directamente. En cambio "1 o 2 baños" es un rango de cosas igualmente
aceptables: estar dentro de él da 100% en ese campo sin importar si es 1 o
2, y alejarse un poco (ej: 3 baños) resta puntaje pero no descalifica. El
score final es el promedio ponderado de todos los campos blandos con datos
disponibles.
