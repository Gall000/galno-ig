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
