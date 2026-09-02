# Notas por portal

Estas notas son un punto de partida, no asesoramiento legal. Revisá siempre
`robots.txt` y los Términos de Servicio vigentes antes de scrapear. Para
varios de los sitios más chicos no tengo información técnica confirmada
(si dependen de JS, si tienen API, etc.) — inspeccionalos vos antes de
implementar el conector.

## Panorama general

A diferencia de postularte a un empleo, mirar avisos de propiedades no
requiere loguearse ni "aplicar" a nada — es información pública que
cualquier visitante ve sin cuenta. Eso baja mucho el riesgo comparado con
automatizar LinkedIn/Indeed, pero igual aplican buenas prácticas:

1. Respetá `robots.txt` de cada sitio.
2. Un rate limit razonable (no varias requests por segundo, con pausas).
3. Identificate con un User-Agent real y de contacto, no simules ser otra
   cosa para evadir bloqueos deliberadamente.
4. Si el sitio ofrece una API pública/oficial, usala en vez de scrapear
   HTML.
5. Si dos de tus fuentes agregan el mismo aviso original (ej: un
   meta-buscador y el portal de origen), vas a ver duplicados — el
   `id`/`source` de `Property` alcanza para filtrarlos si hace falta.

## MercadoLibre Inmuebles

- Sí publica una **API REST pública** (`api.mercadolibre.com`), sin
  necesidad de autenticación para consultas de lectura básicas. Es el
  punto de partida más sólido de los doce: conviene investigar los IDs de
  categoría de "Inmuebles" vigentes y armar `search_listings` sobre esa
  API en vez de scrapear el HTML.

## Zonaprop

- No publica una API pública oficial para terceros. El scraping de
  resultados de búsqueda es la vía habitual; la página usa bastante
  JavaScript, así que probablemente necesites Playwright/Selenium en vez de
  sólo `requests`.

## Argenprop

- Similar a Zonaprop: sin API pública documentada, resultados renderizados
  con JS.

## RE/MAX Argentina (remax.com.ar)

- Franquicia grande con múltiples oficinas/agentes publicando avisos. Sin
  API pública confirmada; probablemente haga falta scrapear los resultados
  de búsqueda.

## Mudafy (mudafy.com.ar)

- Proptech orientada a compra/venta directa. Sin API pública confirmada.

## CABAProp (cabaprop.com.ar)

- Portal/inmobiliaria enfocada en CABA, más chico que los anteriores.
  Inspeccioná el sitio directamente antes de decidir el enfoque.

## BuscadorProp (buscadorprop.com.ar)

- Por el nombre, podría ser un meta-buscador que agrega avisos de otros
  portales — revisá si termina duplicando lo que ya sacás de otra fuente
  antes de sumarlo.

## Toribio Achával (toribioachaval.com)

- Inmobiliaria tradicional de Buenos Aires. Sin información técnica
  confirmada.

## Inmuebles Clarín (inmuebles.clarin.com)

- Sección de clasificados inmobiliarios del diario Clarín. Sin información
  técnica confirmada.

## Solo Dueños (soloduenos.com)

- Avisos publicados directamente por propietarios, sin inmobiliaria
  intermediaria. Sin información técnica confirmada.

## Busca Inmueble (buscainmueble.com)

- Sin información técnica confirmada.

## Lepore Propiedades (lepore.com.ar)

- Inmobiliaria. Sin información técnica confirmada.

## Agregar un portal nuevo

Mismo patrón que los demás: heredar `RealEstateConnector`
(`connectors/base.py`), implementar `search_listings`, registrarlo en
`CONNECTOR_REGISTRY` (`cli.py`), y documentar acá cualquier particularidad
de ToS/API del sitio nuevo. Ver `docs/CONTRIBUIR.md`.
