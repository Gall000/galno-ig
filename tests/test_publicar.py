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


def test_pendientes_marca_vencido_mas_de_13h(tmp_path):
    pub, ven = pendientes([_post(tmp_path, "viejo", 13.5)], AHORA)
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
    assert url_publica(p, "01.jpg", BASE + "/").startswith(f"{BASE}/cola/2026-11-17-mar-demo/01.jpg?v=")


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
    assert _form(responses.calls[0])["image_url"].startswith(f"{BASE}/cola/a/01.jpg?v=")
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


def test_ci_sin_credenciales_modo_prueba(tmp_path, monkeypatch, capsys):
    from galno_ig import ci

    _post(tmp_path, "a")
    for v in ("IG_USER_ID", "IG_TOKEN"):
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setenv("BASE_URL", BASE)
    assert ci.main(raiz=tmp_path, subir=False, ahora=AHORA) == 0
    assert "modo prueba" in capsys.readouterr().out
    assert cargar_post(tmp_path / "cola" / "a").estado == "aprobado"


def test_ci_sale_1_si_hay_error(tmp_path, monkeypatch):
    from galno_ig import ci

    _post(tmp_path, "a")
    monkeypatch.setenv("IG_USER_ID", "IG")
    monkeypatch.setenv("IG_TOKEN", "T")
    monkeypatch.setenv("BASE_URL", BASE)
    with responses.RequestsMock() as rs:
        rs.post(f"{G}/IG/media", status=400, json={"error": {"message": "x"}})
        assert ci.main(raiz=tmp_path, subir=False, ahora=AHORA, verificar_url=lambda u, t: True) == 1


# --- correcciones de la revisión final ---------------------------------------

def _reel_esperando(raiz, id="reel", hace_h=0.1, **cambios):
    datos = dict(tipo="reel", archivos=["reel.mp4"], estado="borrador", necesita_audio=True,
                 extra={"contenido_aprobado": True})
    datos.update(cambios)
    return _post(raiz, id, hace_h, **datos)


def test_reel_ya_vencido_no_gasta_otra_reserva(tmp_path):
    reel = _reel_esperando(tmp_path, estado="vencido")
    res = _post(tmp_path, "res", 48, reserva=True)
    assert pendientes([res, reel], AHORA) == ([], [])


def test_reel_aprobado_sin_audio_nunca_sale(tmp_path):
    reel = _reel_esperando(tmp_path, estado="aprobado")
    pub, _ = pendientes([reel], AHORA)
    assert pub == []


def test_atraso_de_12_y_media_horas_todavia_sale(tmp_path):
    pub, ven = pendientes([_post(tmp_path, "a", 12.5)], AHORA)
    assert ids(pub) == ["a"] and ven == []


def test_url_publica_lleva_version_del_contenido(tmp_path):
    p = _post(tmp_path, "a")
    u1 = url_publica(p, "01.jpg", BASE)
    (p.carpeta / "01.jpg").write_bytes(b"otro contenido")
    u2 = url_publica(p, "01.jpg", BASE)
    assert u1.startswith(f"{BASE}/cola/a/01.jpg?v=") and u1 != u2


def test_si_pages_no_tiene_el_archivo_no_publica(tmp_path):
    _post(tmp_path, "a")
    log = correr(tmp_path, AHORA, Meta("IG", "T"), BASE, verificar_url=lambda url, tam: False)
    assert cargar_post(tmp_path / "cola" / "a").estado == "aprobado"
    assert any("Pages" in x for x in log)


@responses.activate
def test_si_falla_subir_publicando_no_publica(tmp_path):
    _post(tmp_path, "a")

    def falla():
        raise RuntimeError("push rechazado")

    log = correr(tmp_path, AHORA, Meta("IG", "T"), BASE, al_guardar=falla)
    assert len(responses.calls) == 0
    assert cargar_post(tmp_path / "cola" / "a").estado == "aprobado"
    assert any(x.startswith("ERROR") for x in log)


def test_post_yaml_roto_no_frena_los_demas(tmp_path):
    _post(tmp_path, "a")
    roto = tmp_path / "cola" / "roto"
    roto.mkdir()
    (roto / "post.yaml").write_text("tipo: imagen\n", encoding="utf-8")
    log = correr(tmp_path, AHORA, None, BASE)
    assert any("publicaría a" in x for x in log)
    assert any(x.startswith("ERROR roto") for x in log)


def test_ci_modo_prueba_con_algo_pendiente_avisa(tmp_path, monkeypatch):
    from galno_ig import ci

    _post(tmp_path, "a")
    for v in ("IG_USER_ID", "IG_TOKEN"):
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setenv("BASE_URL", BASE)
    monkeypatch.setenv("FALLAR_SIN_CREDENCIALES", "1")
    assert ci.main(raiz=tmp_path, subir=False, ahora=AHORA) == 1


def test_ci_vencido_sale_1(tmp_path, monkeypatch):
    from galno_ig import ci

    _post(tmp_path, "viejo", 30)
    monkeypatch.setenv("IG_USER_ID", "IG")
    monkeypatch.setenv("IG_TOKEN", "T")
    monkeypatch.setenv("BASE_URL", BASE)
    assert ci.main(raiz=tmp_path, subir=False, ahora=AHORA, verificar_url=lambda u, t: True) == 1
