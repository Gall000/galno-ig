"""Semana: vista para aprobar, aprobación y exportación para Meta Business Suite (plan B)."""
from __future__ import annotations

import html
import shutil
from datetime import date, datetime, timedelta
from pathlib import Path

from galno_ig.cola import Post, caption, guardar_post, validar

DIAS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]


def posts_de_semana(cola: list[Post], lunes: date) -> list[Post]:
    """Publicaciones con fecha local (la de su propia zona) entre ese lunes y el domingo."""
    domingo = lunes + timedelta(days=6)
    return [p for p in cola if lunes <= p.fecha_hora.date() <= domingo]


def aprobar(post: Post) -> None:
    problemas = validar(post)
    if problemas:
        raise ValueError(f"{post.id}: " + "; ".join(problemas))
    if post.necesita_audio:
        # El contenido queda aprobado, pero sale recién cuando se cargue el audio.
        post.extra["contenido_aprobado"] = True
        post.estado = "borrador"
    else:
        post.estado = "aprobado"
    guardar_post(post)


def _miniatura(p: Post) -> str:
    if not p.archivos:
        return "<div class='vacio'>sin archivo</div>"
    ruta = (Path(p.carpeta) / p.archivos[0]).resolve()
    if p.tipo == "reel":
        return f"<video src='{ruta.as_uri()}' controls muted preload='metadata'></video>"
    if p.tipo == "carrusel":
        imgs = "".join(f"<img src='{(Path(p.carpeta) / a).resolve().as_uri()}' alt=''>" for a in p.archivos)
        return f"<div class='tira'>{imgs}</div>"
    return f"<img src='{ruta.as_uri()}' alt=''>"


def vista_html(posts: list[Post], salida: Path) -> Path:
    tarjetas = []
    for p in posts:
        problemas = validar(p)
        extra = []
        if p.tipo == "carrusel":
            extra.append(f"{len(p.archivos)} slides")
        if p.necesita_audio:
            extra.append("falta audio")
        if p.ejemplo:
            extra.append("negocio de ejemplo")
        probs = "".join(f"<li>{html.escape(x)}</li>" for x in problemas)
        tarjetas.append(f"""
<article class="{p.estado}">
  <header><b>{DIAS[p.fecha_hora.weekday()]} {p.fecha_hora:%d/%m %H:%M}</b> · {p.tipo} · <span class="estado">{p.estado}</span></header>
  {_miniatura(p)}
  <p class="id">{html.escape(p.id)} {('· ' + ', '.join(extra)) if extra else ''}</p>
  <pre>{html.escape(caption(p))}</pre>
  {f'<ul class="prob">{probs}</ul>' if probs else ''}
</article>""")
    doc = f"""<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"><title>Semana Galno IG</title>
<style>
body{{font-family:"Segoe UI",Arial,sans-serif;margin:24px;background:#f5f5f5;color:#111}}
main{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:18px}}
article{{background:#fff;border:1px solid #ddd;padding:12px}}
article.aprobado{{border-color:#1a7f37}} article.error{{border-color:#c00}}
img,video{{width:100%;aspect-ratio:4/5;object-fit:cover;background:#eee;display:block;margin:8px 0}}
video{{aspect-ratio:9/16}}
.tira{{display:flex;overflow-x:auto;gap:6px;scroll-snap-type:x mandatory}} .tira img{{flex:0 0 100%;scroll-snap-align:start}}
pre{{white-space:pre-wrap;font-family:inherit;font-size:13px;background:#fafafa;padding:8px;margin:0}}
.id{{font-size:12px;color:#666}} .prob{{color:#c00;font-size:13px}} .estado{{text-transform:uppercase;font-size:12px}}
</style></head><body><h1>Semana para aprobar</h1><main>{''.join(tarjetas)}</main></body></html>"""
    salida = Path(salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(doc, encoding="utf-8")
    return salida


def exportar_business_suite(posts: list[Post], salida_dir: Path) -> Path:
    """Copia los archivos numerados y escribe programar.txt para cargarlo a mano en Business Suite."""
    salida_dir = Path(salida_dir)
    salida_dir.mkdir(parents=True, exist_ok=True)
    lineas = ["Programar en Meta Business Suite (hora de Argentina)", ""]
    for n, p in enumerate(posts, start=1):
        nombres = []
        for a in p.archivos:
            destino = salida_dir / f"{n:02d}-{p.id}-{a}"
            shutil.copy2(Path(p.carpeta) / a, destino)
            nombres.append(destino.name)
        lineas += [
            f"== {n:02d} · {DIAS[p.fecha_hora.weekday()]} {p.fecha_hora:%d/%m} {p.fecha_hora:%H:%M} · {p.tipo} · {p.estado}",
            "Archivos: " + ", ".join(nombres),
            "",
            caption(p),
            "",
        ]
    (salida_dir / "programar.txt").write_text("\n".join(lineas), encoding="utf-8")
    return salida_dir


def lunes_de(d: date | datetime) -> date:
    d = d.date() if isinstance(d, datetime) else d
    return d - timedelta(days=d.weekday())
