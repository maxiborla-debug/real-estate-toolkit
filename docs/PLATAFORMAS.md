# Notas por portal

Estas notas son un punto de partida, no asesoramiento legal. Revisá siempre
`robots.txt` y los Términos de Servicio vigentes antes de scrapear.

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

## Zonaprop

- No publica una API pública oficial para terceros. El scraping de
  resultados de búsqueda es la vía habitual; la página usa bastante
  JavaScript, así que probablemente necesites Playwright/Selenium en vez de
  sólo `requests`.

## Argenprop

- Similar a Zonaprop: sin API pública documentada, resultados renderizados
  con JS. Mismas recomendaciones de rate limiting.

## MercadoLibre Inmuebles

- MercadoLibre sí publica una **API REST pública** para búsquedas por
  categoría (`api.mercadolibre.com`), sin necesidad de autenticación para
  consultas de lectura básicas. Es el punto de partida más sólido de los
  cuatro: conviene investigar los IDs de categoría de "Inmuebles" vigentes
  y armar `search_listings` sobre esa API en vez de scrapear el HTML.

## Properati

- Sitio orientado a datos abiertos de mercado inmobiliario; históricamente
  publicó datasets/APIs para investigación. Verificá qué expone actualmente
  antes de decidir entre API o scraping del sitio de avisos.

## Agregar un portal nuevo

Mismo patrón que los otros: heredar `RealEstateConnector`
(`connectors/base.py`), implementar `search_listings`, y documentar acá
cualquier particularidad de ToS/API del sitio nuevo.
