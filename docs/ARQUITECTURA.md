# Arquitectura

## Flujo general (una corrida del cron diario)

```
Config (config.yaml + secrets de email)
        │
        ▼
Cotización del día (fx.get_ars_per_usd) ── se pide UNA vez por corrida
        │
        ▼
Por cada PERFIL (Compra, Alquiler, ...):
        │
        ├─► Por cada fuente activa: Connector.search_listings(criteria) ──► [Property, ...]
        │
        ├─► matching.rank_properties(properties, criteria)
        │     - filtros duros: operación, tipo, zona, precio (convertido a
        │       la moneda del perfil si hace falta), ambientes, dormitorios,
        │       baños (mínimo), m2, exterior obligatorio, apto crédito
        │       (si se pidió)
        │     - dentro de esos filtros, algunos campos gradúan el score:
        │       m2 y baños ("bigger_is_better"), zona y orientación
        │       (preferencia por niveles), parking (bonus)
        │
        ├─► Propiedades con score >= min_score, ordenadas de mayor a menor
        │
        ├─► SeenStore (data/seen_<operacion>.json): separa nuevas vs ya vistas
        │
        └─► notifier.send_email(nuevas) ──► UN mail para este perfil
        │
        ▼
SeenStore.save() de cada perfil ──► se commitean de vuelta al repo (workflow)
```

Cada perfil es independiente de punta a punta: tiene su propio precio,
moneda, destinatario y su propio archivo de "ya vistos" — así una
propiedad nunca aparece mezclada entre el mail de Compra y el de Alquiler,
y un perfil sin novedades no genera mail ese día aunque el otro sí.

## Piezas

- **`models.py`**: `Property`, el modelo normalizado de un aviso, sin
  importar el portal de origen. Incluye una propiedad calculada `m2`
  (total si el aviso lo informa, sino cubierto).
- **`config.py`**:
  - `RangeCriterion`: un rango con dos modos — blando (`hard=False`, decae
    con tolerancia fuera del rango) o duro (`hard=True`, descarta fuera del
    rango; si además `bigger_is_better=True`, gradúa el score dentro del
    rango en vez de dar 1.0 plano).
  - `RequiredFeatureCriterion`: "al menos uno de esta lista, sino se
    descarta" (usado para balcón/terraza/patio/jardín).
  - `TieredPreferenceCriterion`: niveles de preferencia que suman score sin
    excluir (usado para orientación).
  - `SharedCriteria`: todo lo que es igual para todos los perfiles (zonas,
    ambientes, dormitorios, baños, m2, exterior, orientación, parking).
  - `ProfileConfig`: lo que cambia por operación (precio, moneda,
    destinatario, si exige apto crédito).
  - `AppConfig.criteria_for(profile, ars_per_usd)`: combina `SharedCriteria`
    + un `ProfileConfig` en un único `SearchCriteria` listo para matchear.
- **`fx.py`**: cotización del dólar del día (API pública de DolarAPI, con
  valor de respaldo si falla), para poder comparar un aviso publicado en la
  "moneda equivocada" para un perfil (ej: un alquiler en USD contra un
  rango en ARS) en vez de descartarlo directamente.
- **`geo.py`**: distancia entre coordenadas (haversine), para el matching
  por círculos geográficos (alternativa a filtrar por nombre de barrio).
- **`matching.py`**: el corazón del sistema — `score_property` calcula
  0-100% por aviso; `rank_properties` filtra por `min_score` y ordena.
- **`storage.py`**: `SeenStore`, un registro JSON de IDs ya vistos por
  perfil, para que a partir del segundo día sólo se manden novedades.
- **`notifier.py`**: arma y manda el email (HTML) de un perfil vía SMTP de
  Gmail — asunto y destinatario propios de ese perfil.
- **`connectors/`**: un módulo por portal, misma interfaz
  (`RealEstateConnector`).
- **`cli.py`**: `scan` (corre todos los perfiles) y `config-check` (valida
  configuración sin scrapear nada).

## Por qué tantos campos son "filtro duro"

Pediste que ambientes, dormitorios, baños (mínimo), m2 y exterior
obligatorio se comporten como cortes estrictos: si no cumplen, no tiene
sentido mostrar la propiedad con "70% de match" — se descarta. Dentro de
esos cortes, m2 y baños todavía gradúan el score ("cuanto más grande/más
baños, mejor"), pero nunca por debajo del piso exigido. Zona y orientación,
en cambio, no excluyen (más allá de que zona ya filtra qué barrios entran):
sólo hacen que las opciones más deseadas floten más arriba en el mail.
