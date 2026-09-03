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

## Estado real por sitio (probado desde GitHub Actions)

Se probó cada sitio de dos formas: un `GET` simple (`requests`) y un
navegador real headless (Playwright/Chromium) — ver `probe.py` y el comando
`probe-sites [--browser]`. El proyecto corre ahora en un **self-hosted
runner** (tu computadora, ver `docs/DESPLIEGUE.md`) precisamente porque
varios de estos bloqueos son por reputación de IP de datacenter, algo que
ni el navegador real soluciona.

| Sitio | GET simple | Navegador | Notas |
|---|---|---|---|
| MercadoLibre (web) | ✅ limpio | ✅ limpio | La *web* no bloquea; su API de búsqueda (`api.mercadolibre.com`) sí devuelve 403 desde IPs de datacenter — confirmado. |
| RE/MAX | ✅ limpio | ✅ limpio | Angular con SSR; trae bastante data embebida en `ng-state`. API real encontrada: `api-ar.redremax.com` (`/api/listings/findTotalResultByLanding/<slug>` confirmado; el endpoint de resultados completos todavía no). |
| Mudafy | ✅ limpio | ✅ limpio | Sin investigar en profundidad todavía. |
| Solo Dueños | ✅ limpio | ✅ limpio | React + Supabase. Tabla real `properties` confirmada, pero bloqueada por Row Level Security para el rol anónimo — hace falta encontrar el RPC público que usa el buscador (se vio `H.rpc("sear...` en el bundle, truncado). |
| Lepore | ✅ limpio | ✅ limpio | SPA sobre una plataforma SaaS de terceros ("Cliksi", assets en `cliksi-saas-base.s3.amazonaws.com`) — sin investigar su API interna todavía. |
| Zonaprop | ✅ limpio | ❌ **detecta el navegador headless** | Caso interesante: un GET simple pasa sin problema, pero Playwright dispara su detección de bots (probablemente por fingerprint de Chromium automatizado). Con `requests` simple sería el camino, sin renderizar JS — falta confirmar si trae los datos en el HTML crudo o los carga después por JS. |
| Argenprop | ❌ 405 | ⚠️ pasa pero cae en un desafío | Con navegador ya no es un bloqueo duro (405→200) pero el contenido es una página de challenge genérica (10 KB), no los resultados reales. |
| Inmuebles Clarín | ❌ 405 | ⚠️ ídem | Misma página de challenge genérica (10 KB) que Argenprop y Busca Inmueble — probablemente comparten el mismo servicio de protección. |
| Busca Inmueble | ❌ 405 | ⚠️ ídem | Ídem. |
| CABAProp | ⚠️ desafío | ⚠️ desafío (sin cambios) | Ni el GET simple ni el navegador headless lo pasan. |
| BuscadorProp | ⚠️ desafío | ⚠️ desafío (sin cambios) | Ídem. |
| Toribio Achával | ⚠️ desafío | ⚠️ desafío (sin cambios) | Ídem. |

**Lectura práctica**: los 5 primeros (MercadoLibre, RE/MAX, Mudafy, Solo
Dueños, Lepore) no tienen ningún bloqueo — son pura implementación normal.
Zonaprop necesita el enfoque contrario (sin navegador). Los otros 6 son los
candidatos a probar con el runner en tu computadora (IP residencial) antes
de invertir más tiempo — si con eso tampoco pasan, puede hacer falta además
un plugin anti-detección tipo `playwright-stealth`.

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

### Zonaprop, Argenprop

Sin API pública documentada. Zonaprop parece aceptar un `GET` simple sin
JS; Argenprop bloquea con 405 salvo con navegador (y ahí cae en un
challenge). Quedan pendientes de implementación real.

### CABAProp, BuscadorProp, Toribio Achával, Inmuebles Clarín, Busca Inmueble

Los cinco resisten tanto `requests` como Playwright headless. Candidatos a
reintentar una vez que el scan corra desde una IP residencial (self-hosted
runner).

## Agregar un portal nuevo

Mismo patrón que los demás: heredar `RealEstateConnector`
(`connectors/base.py`), implementar `search_listings`, registrarlo en
`CONNECTOR_REGISTRY` (`cli.py`), y documentar acá cualquier particularidad
de ToS/API del sitio nuevo. Usá `probe-sites [--browser]` y `fetch-url
[--browser]` para investigar antes de escribir el parser — ver
`docs/CONTRIBUIR.md`.
