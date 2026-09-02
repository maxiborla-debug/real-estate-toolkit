# Cómo sumar un portal nuevo

1. Creá `src/realestate/connectors/<portal>.py`.
2. Heredá de `RealEstateConnector` (`connectors/base.py`) e implementá
   `search_listings(criteria) -> list[Property]`.
3. Normalizá los campos del portal al modelo `Property` — si un dato no
   existe en ese portal, dejalo en `None`/lista vacía en vez de inventarlo
   (el motor de matching ya sabe ignorar campos sin dato, no los penaliza).
4. Documentá en `docs/PLATAFORMAS.md` cualquier particularidad de ese portal
   (API pública, JS pesado, límites de rate).
5. Registrá el conector en `CONNECTOR_REGISTRY` (`cli.py`) y sumalo a
   `sources` en `config/config.example.yaml` si tiene sentido como opción
   por defecto del proyecto.
6. Sumá tests en `tests/` mockeando la respuesta del portal — no hace falta
   pegarle al sitio real en los tests.

## Estilo

Mismo criterio que el resto del proyecto: nombres de código en inglés,
documentación en español.

## Pull requests

Si vas a compartir tu adaptación de vuelta al repo original: describí qué
portal/funcionalidad agregás y qué probaste (tests, `--dry-run` local).
