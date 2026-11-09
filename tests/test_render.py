from PIL import Image

from galno_ig.render import html_de, render_carrusel, render_imagen


def test_render_imagen_jpeg_1080x1350(tmp_path):
    salida = render_imagen(
        "placa",
        {"etiqueta": "Idea", "titulo": "Tu cliente no quiere llamarte.", "bajada": "Quiere ver el precio y pedir.", "fondo": "oscuro"},
        tmp_path / "placa.jpg",
    )
    with Image.open(salida) as img:
        assert img.format == "JPEG"
        assert img.size == (1080, 1350)
    assert salida.stat().st_size < 8 * 1024 * 1024


def test_render_carrusel_numera(tmp_path):
    slides = [{"etiqueta": "Consejo", "titulo": f"Slide {i}", "cuerpo": "Texto"} for i in range(3)]
    rutas = render_carrusel(slides, tmp_path)
    assert [r.name for r in rutas] == ["01.jpg", "02.jpg", "03.jpg"]
    with Image.open(rutas[0]) as img:
        assert img.size == (1080, 1350)


def test_ejemplo_visible():
    assert "Negocio de ejemplo" in html_de("placa", {"titulo": "x", "ejemplo": True})
    assert "Negocio de ejemplo" not in html_de("placa", {"titulo": "x"})


# --- Marca Galno 2.0 ---
from galno_ig.render import PLANTILLAS

TRAZO_G = "M71 26C63 16 49.5 12.5 37.5 17.5"  # primer tramo de la G oficial (Marca/galno-simbolo-*.svg)


def test_usa_logo_oficial_y_no_el_viejo():
    for plantilla in ("placa", "carrusel", "reel-demo", "reel-antes-despues"):
        html = html_de(plantilla, {"titulo": "x", "items": [], "antes": [], "turnos": [], "duracion_ms": 1000})
        assert TRAZO_G in html, plantilla
        assert "M0 0H24V5" not in html, plantilla  # G de bloques de la 1.0


def test_tipografia_schibsted():
    css = (PLANTILLAS / "tema.css").read_text(encoding="utf-8")
    assert "Schibsted Grotesk" in css
    assert (PLANTILLAS / "fuentes" / "SchibstedGrotesk.ttf").exists()


def test_acento_en_lacre_y_escapa_html():
    html = html_de("placa", {"titulo": "Tu cliente no quiere <b>llamarte</b>.", "acento": "llamarte"})
    assert '<span class="lacre">llamarte</span>' in html
    assert "&lt;b&gt;" in html


def test_lacre_una_sola_vez():
    con = html_de("placa", {"titulo": "Tu cliente no quiere llamarte.", "acento": "llamarte"})
    sin = html_de("placa", {"titulo": "Tu cliente no quiere llamarte."})
    assert 'flecha lacre' not in con  # el acento ya usó el lacre: la flecha va en tinta
    assert 'flecha lacre' in sin


def test_dibujo_por_rubro():
    assert 'data-dibujo="reloj"' in html_de("placa", {"titulo": "x", "dibujo": "reloj"})
    assert "data-dibujo" not in html_de("placa", {"titulo": "x"})
