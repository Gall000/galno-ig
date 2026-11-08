from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from galno_ig.cola import Post, caption, cargar_cola, cargar_post, guardar_post, validar

AR = timezone(timedelta(hours=-3))


def _escribir(carpeta: Path, contenido: str) -> Path:
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / "post.yaml").write_text(contenido, encoding="utf-8")
    return carpeta


def _post(tmp_path: Path, **cambios) -> Post:
    carpeta = tmp_path / cambios.pop("id", "2026-11-16-lun-consejo")
    carpeta.mkdir(parents=True, exist_ok=True)
    datos = dict(
        id=carpeta.name,
        carpeta=carpeta,
        fecha_hora=datetime(2026, 11, 16, 8, 30, tzinfo=AR),
        tipo="imagen",
        archivos=["01.jpg"],
        texto="Escribime por DM",
        hashtags=["negocioslocales", "olivos"],
        estado="borrador",
    )
    datos.update(cambios)
    for a in datos["archivos"]:
        (carpeta / a).write_bytes(b"x")
    return Post(**datos)


YAML = """fecha_hora: '2026-11-16T08:30:00-03:00'
tipo: carrusel
archivos: [01.jpg, 02.jpg]
texto: Consejo del lunes
hashtags: [negocioslocales, olivos]
estado: aprobado
ejemplo: false
"""


def test_carga_y_guarda_ida_y_vuelta(tmp_path):
    carpeta = _escribir(tmp_path / "2026-11-16-lun-consejo", YAML)
    p = cargar_post(carpeta)
    assert p.id == "2026-11-16-lun-consejo"
    assert p.fecha_hora == datetime(2026, 11, 16, 8, 30, tzinfo=AR)
    assert p.tipo == "carrusel" and p.archivos == ["01.jpg", "02.jpg"]
    p.estado = "publicado"
    p.media_id = "123"
    guardar_post(p)
    q = cargar_post(carpeta)
    assert q.estado == "publicado" and q.media_id == "123"
    assert q.fecha_hora == p.fecha_hora and q.texto == p.texto and q.hashtags == p.hashtags


@pytest.mark.parametrize("n", [0, 4])
def test_validar_hashtags_fuera_de_rango(tmp_path, n):
    p = _post(tmp_path, hashtags=[f"h{i}" for i in range(n)])
    assert any("hashtags" in x for x in validar(p))


def test_validar_ok(tmp_path):
    assert validar(_post(tmp_path)) == []


def test_validar_ejemplo_sin_aviso(tmp_path):
    p = _post(tmp_path, ejemplo=True, texto="Así pide un cliente")
    assert validar(p)
    p2 = _post(tmp_path, id="otro", ejemplo=True, texto="Negocio de ejemplo. Así pide un cliente")
    assert validar(p2) == []


def test_validar_archivo_faltante(tmp_path):
    p = _post(tmp_path)
    (p.carpeta / "01.jpg").unlink()
    assert any("01.jpg" in x for x in validar(p))


def test_validar_imagen_no_jpg(tmp_path):
    p = _post(tmp_path, archivos=["01.png"])
    assert validar(p)


@pytest.mark.parametrize("n", [1, 21])
def test_validar_carrusel_1_o_21_items(tmp_path, n):
    p = _post(tmp_path, tipo="carrusel", archivos=[f"{i:02d}.jpg" for i in range(1, n + 1)])
    assert any("carrusel" in x for x in validar(p))


def test_validar_reel_un_mp4(tmp_path):
    assert validar(_post(tmp_path, tipo="reel", archivos=["reel.mp4"])) == []
    assert validar(_post(tmp_path, id="b", tipo="reel", archivos=["reel.mp4", "otro.mp4"]))
    assert validar(_post(tmp_path, id="c", tipo="reel", archivos=["01.jpg"]))


def test_caption(tmp_path):
    p = _post(tmp_path, texto="Hola", hashtags=["a", "b", "c"])
    assert caption(p) == "Hola\n\n#a #b #c"


def test_cargar_cola_ordena(tmp_path):
    _escribir(tmp_path / "b", YAML.replace("2026-11-16T08:30", "2026-11-18T20:00"))
    _escribir(tmp_path / "a", YAML.replace("2026-11-16T08:30", "2026-11-17T20:00"))
    _escribir(tmp_path / "c", YAML)
    (tmp_path / ".gitkeep").write_text("")
    assert [p.id for p in cargar_cola(tmp_path)] == ["c", "a", "b"]
