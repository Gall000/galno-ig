"""Render de plantillas HTML a JPEG 1080×1350 con Playwright."""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, Undefined, select_autoescape
from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parent.parent
PLANTILLAS = RAIZ / "plantillas"
ANCHO, ALTO = 1080, 1350

_env = Environment(
    loader=FileSystemLoader(PLANTILLAS),
    autoescape=select_autoescape(["html"]),
    undefined=Undefined,  # campos faltantes = vacío, no error
)


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
