# Galno IG

Contenido y publicación del Instagram de Galno Assist.

- `plantillas/`: plantillas HTML con la marca Galno 2.0 (guía canónica en el vault, §15). Colores y tipografía en `tema.css` y `reel.css`; logos oficiales en `marca/`; dibujos en `_dibujos.html`. Campos útiles: `fondo` (claro|oscuro, alternar en la grilla), `acento` (palabra del título en lacre, una por pieza), `dibujo` (tijera, taza, pizza, llave, pan, servilleta, reloj, cartel).
- `cola/<id>/`: una carpeta por publicación con `post.yaml`, archivos (`.jpg` / `.mp4`) y, en reels, `reel.yaml` + `guion.md`.
- `galno_ig/`: render, cola, vista semanal, publicador.
- `.github/workflows/publicar.yml`: publica sola lo **aprobado**, 4 veces por día, con la API oficial de Meta.

## Uso semanal

```bash
.venv/Scripts/python -m galno_ig semana 2026-11-16      # vista para aprobar (salida/semana-....html)
.venv/Scripts/python -m galno_ig aprobar <id> <id> ...  # sólo lo aprobado se publica
.venv/Scripts/python -m galno_ig audio <id> voz.m4a     # domingo: carga la voz de un reel
.venv/Scripts/python -m galno_ig exportar 2026-11-16    # plan B: carpeta para Business Suite
```

Estados: `borrador` → `aprobado` → `publicando` → `publicado` (o `error` / `vencido`).
Un reel sin voz nunca sale: a su hora sale una publicación de reserva (`reserva: true`).

Acceso a Meta: ver `LEEME-meta.md`.
