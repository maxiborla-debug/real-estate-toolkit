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
3. Identificate con un User-Agent real, no simules ser otra cosa para
   evadir bloqueos deliberadamente.
4. Si el sitio ofrece una API pública/oficial, usala en vez de scrapear
   HTML.

## Estado real por sitio (actualizado: probado desde tu runner residencial)

Se probó cada sitio de dos formas: un `GET` simple (`requests`) y un
navegador real headless (Playwright/Chromium) — ver `probe.py` y el comando
`probe-sites [--browser]`.

**Resultado final, desde tu Mac (IP residencial) con navegador real: los 12
sitios devuelven 200 con el contenido completo, sin ninguna señal de
bloqueo.** Esto contradice una conclusión anterior de este documento (ver
nota histórica abajo) — la sonda tenía un heurístico de detección de
bloqueo demasiado amplio (marcaba "captcha" o "cloudflare" como señal de
bloqueo, pero esas palabras también aparecen en features normales como un
widget de reCAPTCHA de un formulario de login), y eso generaba falsos
positivos. Corregido en `probe.py` (`_BLOCK_MARKERS`).

| Sitio | GET simple (desde GitHub Actions) | Navegador (desde tu runner residencial) |
|---|---|---|
| MercadoLibre (web) | ✅ limpio | ✅ limpio |
| RE/MAX | ✅ limpio | ✅ limpio |
| Mudafy | ✅ limpio | ✅ limpio |
| Solo Dueños | ✅ limpio | ✅ limpio |
| Lepore | ✅ limpio | ✅ limpio |
| Zonaprop | ✅ limpio | ✅ limpio |
| Argenprop | ❌ 405 (IP datacenter) | ✅ limpio |
| Inmuebles Clarín | ❌ 405 (IP datacenter) | ✅ limpio |
| Busca Inmueble | ❌ 405 (IP datacenter) | ✅ limpio |
| CABAProp | ⚠️ desafío (IP datacenter) | ✅ limpio |
| BuscadorProp | ⚠️ desafío (IP datacenter) | ✅ limpio |
| Toribio Achával | ⚠️ desafío (IP datacenter) | ✅ limpio |

**Lectura práctica**: la migración al self-hosted runner (IP residencial)
resolvió el problema de reachability para los 12 sitios. Lo que queda
pendiente para cada uno **no es esquivar un bloqueo, es escribir el
parser/conector real** que extraiga los avisos de cada sitio (ver
`docs/CONTRIBUIR.md`) — MercadoLibre y, parcialmente, Solo Dueños y RE/MAX
ya tienen ese trabajo empezado (ver notas específicas abajo).

### Nota histórica (ya resuelta): bloqueo desde la nube de GitHub

Cuando el scan corría en los runners compartidos de GitHub Actions (IP de
datacenter), 6 de los 12 sitios devolvían 405 o una página de desafío
genérica de ~10 KB, tanto con `requests` como con navegador headless — un
bloqueo real por reputación de IP, no arreglable con un cliente más
"parecido a un navegador". Esa fue la razón original para migrar a un
self-hosted runner en tu propia computadora (ver `docs/DESPLIEGUE.md`). La
migración funcionó: ninguno de esos 6 sitios sigue bloqueado.

## Notas específicas

### MercadoLibre

API pública en `api.mercadolibre.com/sites/MLA/search` (categoría
`MLA1459`), documentada y sin necesidad de auth para lectura — pero
bloqueada por IP de datacenter. Conector ya implementado en
`connectors/mercadolibre.py`.

### RE/MAX

Backend real: `api-ar.redremax.com/remaxweb-ar/api/listings/` (Spring Boot).
`findTotalResultByLanding/<slug>` confirmado (sólo da el total); el
endpoint con los resultados completos todavía no se identificó — sería el
próximo paso si se retoma este conector.

### Solo Dueños

React + Supabase. La anon key se extrae en tiempo de ejecución del bundle
principal (nunca se loggea — ver `connectors/soloduenos.py`). La tabla
`properties` está protegida por RLS; falta encontrar el RPC público
(`supabase.rpc(...)`) que usa el buscador del sitio.

### Lepore

Corre sobre una plataforma SaaS ("Cliksi") usada probablemente por más de
una inmobiliaria chica — si se investiga su API interna, el mismo trabajo
podría servir para otros sitios construidos sobre la misma plataforma.

### Zonaprop, Argenprop, CABAProp, BuscadorProp, Toribio Achával, Inmuebles Clarín, Busca Inmueble

Sin API pública documentada todavía. Ya no hay ningún bloqueo de por medio
(ver tabla arriba) — el trabajo pendiente para cada uno es puramente de
implementación: inspeccionar su HTML/JS con `fetch-url [--browser]` para
encontrar cómo extraer los avisos (HTML renderizado, una API interna tipo
la de RE/MAX o Solo Dueños, etc.) y escribir el conector real.

## Agregar un portal nuevo

Mismo patrón que los demás: heredar `RealEstateConnector`
(`connectors/base.py`), implementar `search_listings`, registrarlo en
`CONNECTOR_REGISTRY` (`cli.py`), y documentar acá cualquier particularidad
de ToS/API del sitio nuevo. Usá `probe-sites [--browser]` y `fetch-url
[--browser]` para investigar antes de escribir el parser — ver
`docs/CONTRIBUIR.md`.
