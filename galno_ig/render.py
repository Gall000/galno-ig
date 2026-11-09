"""Render de plantillas HTML a JPEG 1080×1350 con Playwright."""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

import re

from jinja2 import Environment, FileSystemLoader, Undefined, select_autoescape
from markupsafe import Markup, escape
from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parent.parent
PLANTILLAS = RAIZ / "plantillas"
ANCHO, ALTO = 1080, 1350

_env = Environment(
    loader=FileSystemLoader(PLANTILLAS),
    autoescape=select_autoescape(["html"]),
    undefined=Undefined,  # campos faltantes = vacío, no error
)

_TINTA, _BLANCO = "#141414", "#FFFFFF"


def logo(pieza: str, modo: str = "claro", clase: str = "") -> Markup:
    """SVG oficial de Marca/ (simbolo | wordmark | assist), inline y sin tocar los trazos.
    Sólo se cambia el <style> por atributos, para poder mezclar claro y oscuro en una misma página."""
    svg = (PLANTILLAS / "marca" / f"galno-{pieza}-{modo}.svg").read_text(encoding="utf-8")
    color = _BLANCO if modo == "oscuro" else _TINTA
    svg = re.sub(r"<style>.*?</style>", "", svg)
    svg = svg.replace('class="s"', f'class="trazo" stroke="{color}"').replace('class="f"', f'fill="{color}"')
    return Markup(svg.replace("<svg ", f'<svg class="logo {clase}" aria-label="Galno" role="img" ', 1))


def acento(texto, palabra=None) -> Markup:
    """Escapa el texto y pinta en lacre la primera aparición de `palabra` (regla: un acento por pieza)."""
    seguro = str(escape(texto or ""))
    if palabra:
        p = str(escape(palabra))
        seguro = seguro.replace(p, f'<span class="lacre">{p}</span>', 1)
    return Markup(seguro)


_env.globals["logo"] = logo
_env.filters["acento"] = acento


def html_de(plantilla: str, datos: dict) -> str:
    """HTML final de una plantilla, con <base> para que resuelva tema.css."""
    html = _env.get_template(f"{plantilla}.html").render(**datos)
    base = f'<base href="{PLANTILLAS.as_uri()}/">'
    return html.replace("<head>", f"<head>\n{base}", 1)


@contextmanager
def pagina(ancho: int = ANCHO, alto: int = ALTO):
    with sync_playwright() as pw:
        navegador = pw.chromium.launch()
        try:
            yield navegador.new_page(viewport={"width": ancho, "height": alto})
        finally:
            navegador.close()


def _capturar(page, plantilla: str, datos: dict, salida: Path) -> Path:
    salida = Path(salida).resolve()
    salida.parent.mkdir(parents=True, exist_ok=True)
    tmp = salida.with_suffix(".tmp.html")
    tmp.write_text(html_de(plantilla, datos), encoding="utf-8")
    try:
        page.goto(tmp.as_uri())
        page.wait_for_load_state("load")
        page.evaluate("document.fonts.ready.then(() => true)")
        page.screenshot(path=str(salida), type="jpeg", quality=90, full_page=False)
    finally:
        tmp.unlink(missing_ok=True)
    return salida


def render_imagen(plantilla: str, datos: dict, salida: Path) -> Path:
    with pagina() as page:
        return _capturar(page, plantilla, datos, salida)


def render_carrusel(slides: list[dict], salida_dir: Path, plantilla: str = "carrusel") -> list[Path]:
    salida_dir = Path(salida_dir)
    total = len(slides)
    rutas = []
    with pagina() as page:
        for i, datos in enumerate(slides, start=1):
            datos = {"n": i, "total": total, **datos}
            rutas.append(_capturar(page, plantilla, datos, salida_dir / f"{i:02d}.jpg"))
    return rutas
