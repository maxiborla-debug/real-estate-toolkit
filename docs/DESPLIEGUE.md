# Despliegue: correr el scan todos los días a las 17hs

El scan corre en GitHub Actions, sin depender de que tengas una computadora
prendida ni una sesión de Claude abierta.

## 1. Cargar los criterios reales

`config/config.yaml` ya está commiteado con tus criterios (zonas, rangos,
perfiles de Compra/Alquiler). Antes de dejarlo corriendo en serio, revisá
puntualmente:

- El `recipient` de cada perfil en `profiles` — hoy apunta a un mail de
  prueba; cambialo cuando quieras que le llegue a otra persona.
- Que las 12 fuentes en `sources` tengan su conector implementado (ver
  `docs/PLATAFORMAS.md` y `docs/CONTRIBUIR.md`) — mientras no lo estén, el
  scan simplemente las salta y sigue con el resto.

Si en algún momento partís de cero, `config/config.example.yaml` es la
plantilla genérica documentada.

## 2. Generar una contraseña de aplicación de Gmail

1. Activá la verificación en 2 pasos en tu cuenta de Google (si no la tenés).
2. Andá a https://myaccount.google.com/apppasswords
3. Generá una contraseña de aplicación para "Correo" / "Otra (nombre
   personalizado)" — copiá el código de 16 caracteres que te da.

## 3. Cargar los secrets en GitHub

En el repo: **Settings → Secrets and variables → Actions → New repository
secret**, y creá:

- `GMAIL_USER`: tu dirección de Gmail completa.
- `GMAIL_APP_PASSWORD`: la contraseña de aplicación del paso anterior.

Estos valores nunca se ven en los logs del workflow ni se commitean al repo.

## 4. Confirmar el horario

El workflow (`.github/workflows/daily-scan.yml`) corre a las `20:00 UTC`,
que equivale a las `17:00` en Argentina (UTC-3 todo el año, sin horario de
verano). Si en algún momento cambia el huso horario argentino, hay que
ajustar el cron a mano.

## 5. Probar sin esperar al cron

- Localmente: `cp .env.example .env`, completá las credenciales, `pip
  install -e ".[dev]"` y corré `python -m realestate.cli scan --dry-run`
  (no manda mail, sólo muestra qué matchearía).
- En GitHub: pestaña **Actions → Escaneo diario de propiedades → Run
  workflow**, para forzar una corrida real cuando quieras.

## 6. Cómo sigue funcionando día a día

- Primera corrida de cada perfil: `data/seen_venta.json` /
  `data/seen_alquiler.json` no existen → se manda **todo** lo que matchea
  para ese perfil.
- Corridas siguientes: sólo se manda lo que matchea Y no estaba en el
  `seen_<perfil>.json` de la corrida anterior. El workflow los commitea de
  vuelta al repo al final de cada corrida para que la próxima los
  encuentre actualizados.
- Compra y Alquiler son independientes: si un día sólo hay novedades en uno
  de los dos, sólo se manda ese mail.
- Si un conector todavía no está implementado para algún portal, el scan lo
  loggea y sigue con el resto — no se cae toda la corrida por un portal
  pendiente.
- Si no hay novedades nuevas ese día para un perfil, directamente no se
  manda su mail (no hay spam de "0 resultados" todos los días).
- La cotización del dólar se pide una vez por corrida (API pública de
  DolarAPI); si falla, se usa `fx_fallback_ars_per_usd` de `config.yaml`.
