# Despliegue: correr el scan todos los días a las 17hs

El scan corre en **tu computadora**, registrada como "self-hosted runner" de
GitHub Actions — no en la nube compartida de GitHub. Esto es a propósito:
varios portales bloquean las IPs de datacenter que usa la nube de GitHub,
pero no una IP residencial normal como la de tu casa. Ver
`docs/PLATAFORMAS.md` para el detalle de qué sitios lo necesitan.

Esto tiene una contrapartida: el scan diario sólo corre si tu computadora
está prendida y conectada a internet a esa hora. Si no lo está, GitHub deja
la corrida en cola y se dispara sola apenas tu compu se reconecte — no se
pierde, sólo se atrasa.

## 1. Registrar tu computadora como runner

1. En el repo: **Settings → Actions → Runners → New self-hosted runner**.
2. Elegí tu sistema operativo (Linux, macOS o Windows) — GitHub te muestra
   los comandos exactos para descargar e instalar el runner en esa página,
   copialos y correlos tal cual en una terminal.
3. Cuando el script te pregunte, dejá el nombre y las labels por defecto
   (alcanza con la label `self-hosted` que se agrega sola).
4. En vez de dejar la terminal abierta corriendo `./run.sh` (se corta si
   cerrás la terminal o reiniciás), instalalo como servicio para que quede
   corriendo solo:
   - **Linux/macOS**: `sudo ./svc.sh install && sudo ./svc.sh start`
   - **Windows** (como administrador): `.\svc.cmd install` y luego
     `.\svc.cmd start`
5. Confirmá que en **Settings → Actions → Runners** tu máquina aparece con
   un punto verde ("Idle").

**Nota de seguridad**: un self-hosted runner ejecuta el código de este repo
directamente en tu máquina. Es el enfoque recomendado para un repo privado
tuyo (como este), pero nunca lo uses en un repo público donde cualquiera
pueda abrir un Pull Request — ahí sí sería un riesgo real.

**Linux**: la primera vez puede hacer falta instalar dependencias del
sistema para Chromium (el workflow ya no lo hace automático, ver el
comentario en `daily-scan.yml`):
```bash
sudo python -m playwright install-deps chromium
```

## 2. Cargar los criterios reales

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

## 3. Generar una contraseña de aplicación de Gmail

1. Activá la verificación en 2 pasos en tu cuenta de Google (si no la tenés).
2. Andá a https://myaccount.google.com/apppasswords
3. Generá una contraseña de aplicación para "Correo" / "Otra (nombre
   personalizado)" — copiá el código de 16 caracteres que te da.

## 4. Cargar los secrets en GitHub

En el repo: **Settings → Secrets and variables → Actions → New repository
secret**, y creá:

- `GMAIL_USER`: tu dirección de Gmail completa.
- `GMAIL_APP_PASSWORD`: la contraseña de aplicación del paso anterior.

Estos valores nunca se ven en los logs del workflow ni se commitean al repo
(y en un self-hosted runner tampoco quedan guardados en tu disco: GitHub se
los pasa al job en el momento, cifrados).

## 5. Confirmar el horario

El workflow (`.github/workflows/daily-scan.yml`) corre a las `20:00 UTC`,
que equivale a las `17:00` en Argentina (UTC-3 todo el año, sin horario de
verano). Si en algún momento cambia el huso horario argentino, hay que
ajustar el cron a mano.

## 6. Probar sin esperar al cron

- Localmente, sin pasar por GitHub Actions: `cp .env.example .env`, completá
  las credenciales, `pip install -e ".[dev]"` y corré
  `python -m realestate.cli scan --dry-run` (no manda mail, sólo muestra
  qué matchearía).
- En GitHub, ya usando tu runner: pestaña **Actions → Escaneo diario de
  propiedades → Run workflow**, para forzar una corrida real cuando quieras
  (con `dry_run` tildado para no arriesgar mandar nada).

## 7. Cómo sigue funcionando día a día

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
- Si tu computadora está apagada a las 17hs, la corrida queda en cola en
  GitHub y se dispara apenas la prendas y el runner se reconecte.
