import json
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs

import pytest
import responses

from galno_ig.cola import Post, cargar_post, guardar_post
from galno_ig.publicar import Meta, correr, pendientes, url_publica

AR = timezone(timedelta(hours=-3))
AHORA = datetime(2026, 11, 17, 20, 5, tzinfo=AR)
G = "https://graph.facebook.com/v27.0"
BASE = "https://gall000.github.io/galno-ig"


def _post(raiz, id, hace_h=0.1, **cambios):
    carpeta = raiz / "cola" / id
    carpeta.mkdir(parents=True, exist_ok=True)
    datos = dict(id=id, carpeta=carpeta, fecha_hora=AHORA - timedelta(hours=hace_h), tipo="imagen",
                 archivos=["01.jpg"], texto="Hola", hashtags=["olivos"], estado="aprobado")
    datos.update(cambios)
    for a in datos["archivos"]:
        (carpeta / a).write_bytes(b"x")
    p = Post(**datos)
    guardar_post(p)
    return p


def ids(posts):
    return [p.id for p in posts]


# --- pendientes -------------------------------------------------------------

def test_pendientes_toma_aprobados_vencidos_hasta_12h(tmp_path):
    cola = [_post(tmp_path, "a", 0.1), _post(tmp_path, "b", 11.9), _post(tmp_path, "futuro", -1)]
    pub, ven = pendientes(cola, AHORA)
    assert ids(pub) == ["b", "a"] and ven == []


def test_pendientes_marca_vencido_mas_de_12h(tmp_path):
    pub, ven = pendientes([_post(tmp_path, "viejo", 12.5)], AHORA)
    assert pub == [] and ids(ven) == ["viejo"]


def test_pendientes_ignora_borrador_y_publicando(tmp_path):
    cola = [_post(tmp_path, "b", estado="borrador"), _post(tmp_path, "p", estado="publicando"),
            _post(tmp_path, "x", estado="publicado")]
    assert pendientes(cola, AHORA) == ([], [])


def test_reserva_no_sale_en_su_propia_fecha(tmp_path):
    assert pendientes([_post(tmp_path, "res", 1, reserva=True)], AHORA) == ([], [])


def test_reel_sin_audio_usa_reserva(tmp_path):
    reel = _post(tmp_path, "reel", 0.1, tipo="reel", archivos=["reel.mp4"], estado="borrador",
                 necesita_audio=True, extra={"contenido_aprobado": True})
    res = _post(tmp_path, "res", 48, reserva=True)
    pub, ven = pendientes([res, reel], AHORA)
    assert ids(pub) == ["res"]
    assert ids(ven) == ["reel"]


def test_reel_sin_audio_sin_reserva_no_publica_nada(tmp_path):
    reel = _post(tmp_path, "reel", 0.1, tipo="reel", archivos=["reel.mp4"], estado="borrador",
                 necesita_audio=True, extra={"contenido_aprobado": True})
    pub, ven = pendientes([reel], AHORA)
    assert pub == [] and ven == []


# --- Meta -------------------------------------------------------------------

def _form(call):
    return {k: v[0] for k, v in parse_qs(call.request.body).items()}


@responses.activate
def test_crear_imagen_postea_image_url_y_caption():
    responses.post(f"{G}/IG/media", json={"id": "C1"})
    assert Meta("IG", "TOK").crear_imagen("https://x/a.jpg", "Hola") == "C1"
    form = _form(responses.calls[0])
    assert form == {"image_url": "https://x/a.jpg", "caption": "Hola"}
    assert responses.calls[0].request.headers["Authorization"] == "Bearer TOK"


@responses.activate
def test_carrusel_crea_hijos_y_padre():
    responses.post(f"{G}/IG/media", json={"id": "H1"})
    responses.post(f"{G}/IG/media", json={"id": "H2"})
    responses.post(f"{G}/IG/media", json={"id": "PADRE"})
    assert Meta("IG", "T").crear_carrusel(["u1", "u2"], "cap") == "PADRE"
    f = [_form(c) for c in responses.calls]
    assert f[0] == {"image_url": "u1", "is_carousel_item": "true"}
    assert f[2] == {"media_type": "CAROUSEL", "children": "H1,H2", "caption": "cap"}


@responses.activate
def test_crear_reel():
    responses.post(f"{G}/IG/media", json={"id": "R"})
    Meta("IG", "T").crear_reel("https://x/r.mp4", "cap")
    assert _form(responses.calls[0]) == {"media_type": "REELS", "video_url": "https://x/r.mp4",
                                         "caption": "cap", "share_to_feed": "true"}


@responses.activate
def test_esperar_error_lanza():
    responses.get(f"{G}/C1", json={"status_code": "IN_PROGRESS"})
    responses.get(f"{G}/C1", json={"status_code": "ERROR", "status": "Error: formato"})
    with pytest.raises(RuntimeError, match="ERROR"):
        Meta("IG", "T").esperar("C1", intentos=5, pausa_s=0)


@responses.activate
def test_error_de_api_no_filtra_token():
    responses.post(f"{G}/IG/media", status=400, json={"error": {"message": "Invalid parameter"}})
    with pytest.raises(RuntimeError) as e:
        Meta("IG", "SECRETO").crear_imagen("u", "c")
    assert "Invalid parameter" in str(e.value) and "SECRETO" not in str(e.value)


# --- correr -----------------------------------------------------------------

def test_url_publica(tmp_path):
    p = _post(tmp_path, "2026-11-17-mar-demo")
    assert url_publica(p, "01.jpg", BASE + "/") == f"{BASE}/cola/2026-11-17-mar-demo/01.jpg"


@responses.activate
def test_correr_feliz_queda_publicado(tmp_path):
    _post(tmp_path, "a")
    responses.post(f"{G}/IG/media", json={"id": "C1"})
    responses.post(f"{G}/IG/media_publish", json={"id": "M1"})
    estados = []
    log = correr(tmp_path, AHORA, Meta("IG", "T"), BASE,
                 al_guardar=lambda: estados.append(cargar_post(tmp_path / "cola" / "a").estado))
    p = cargar_post(tmp_path / "cola" / "a")
    assert p.estado == "publicado" and p.media_id == "M1"
    assert estados[0] == "publicando"
    assert _form(responses.calls[0])["image_url"] == f"{BASE}/cola/a/01.jpg"
    assert any("publicado" in x for x in log)


@responses.activate
def test_correr_error_queda_error_con_mensaje(tmp_path):
    _post(tmp_path, "a")
    responses.post(f"{G}/IG/media", status=400, json={"error": {"message": "Only photo or video"}})
    correr(tmp_path, AHORA, Meta("IG", "T"), BASE)
    p = cargar_post(tmp_path / "cola" / "a")
    assert p.estado == "error" and "Only photo or video" in p.error


def test_correr_sin_meta_no_cambia_estados(tmp_path):
    _post(tmp_path, "a")
    _post(tmp_path, "viejo", 30)
    log = correr(tmp_path, AHORA, None, BASE)
    assert cargar_post(tmp_path / "cola" / "a").estado == "aprobado"
    assert cargar_post(tmp_path / "cola" / "viejo").estado == "aprobado"
    assert any("modo prueba" in x for x in log)


@responses.activate
def test_correr_marca_vencidos(tmp_path):
    _post(tmp_path, "viejo", 30)
    correr(tmp_path, AHORA, Meta("IG", "T"), BASE)
    assert cargar_post(tmp_path / "cola" / "viejo").estado == "vencido"
    assert len(responses.calls) == 0
