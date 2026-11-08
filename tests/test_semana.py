from datetime import date, datetime, timedelta, timezone

import pytest

from galno_ig.cola import Post, cargar_post
from galno_ig.semana import aprobar, exportar_business_suite, posts_de_semana, vista_html

AR = timezone(timedelta(hours=-3))


def _post(tmp_path, id, dia=16, hora=8, minuto=30, **cambios):
    carpeta = tmp_path / id
    carpeta.mkdir(parents=True, exist_ok=True)
    datos = dict(id=id, carpeta=carpeta, fecha_hora=datetime(2026, 11, dia, hora, minuto, tzinfo=AR),
                 tipo="imagen", archivos=["01.jpg"], texto="Escribime por DM", hashtags=["olivos"],
                 estado="borrador")
    datos.update(cambios)
    for a in datos["archivos"]:
        (carpeta / a).write_bytes(b"x")
    return Post(**datos)


def test_aprobar_rechaza_invalido(tmp_path):
    p = _post(tmp_path, "a", hashtags=[])
    with pytest.raises(ValueError, match="hashtags"):
        aprobar(p)
    assert p.estado == "borrador"


def test_aprobar_guarda_aprobado(tmp_path):
    p = _post(tmp_path, "a")
    aprobar(p)
    assert cargar_post(p.carpeta).estado == "aprobado"


def test_aprobar_reel_sin_audio_queda_borrador(tmp_path):
    p = _post(tmp_path, "r", tipo="reel", archivos=["reel.mp4"], necesita_audio=True)
    aprobar(p)
    q = cargar_post(p.carpeta)
    assert q.estado == "borrador"
    assert q.extra.get("contenido_aprobado") is True


def test_posts_de_semana_lunes_a_domingo(tmp_path):
    cola = [_post(tmp_path, "dom-ant", dia=15, hora=23), _post(tmp_path, "lun", dia=16, hora=0, minuto=0),
            _post(tmp_path, "dom", dia=22, hora=23, minuto=59), _post(tmp_path, "lun-sig", dia=23, hora=0, minuto=0)]
    assert [p.id for p in posts_de_semana(cola, date(2026, 11, 16))] == ["lun", "dom"]


def test_exportar_crea_programar_txt(tmp_path):
    posts = [_post(tmp_path / "cola", "a", texto="Primero"), _post(tmp_path / "cola", "b", dia=17, hora=20, minuto=0, texto="Segundo")]
    destino = exportar_business_suite(posts, tmp_path / "export")
    txt = (destino / "programar.txt").read_text(encoding="utf-8")
    assert "Primero" in txt and "Segundo" in txt
    assert "08:30" in txt and "20:00" in txt
    assert (destino / "01-a-01.jpg").exists() and (destino / "02-b-01.jpg").exists()


def test_vista_html_incluye_problemas(tmp_path):
    p = _post(tmp_path, "a", hashtags=[])
    html = vista_html([p], tmp_path / "vista.html").read_text(encoding="utf-8")
    assert "hashtags" in html and "a" in html
