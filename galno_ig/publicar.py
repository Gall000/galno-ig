"""Publicador con la Instagram Content Publishing API oficial (Facebook Login, graph.facebook.com).

Sólo publica lo que Lucas aprobó. Nunca loguea el token.
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable

import requests

from galno_ig.cola import Post, caption, cargar_cola, guardar_post

ATRASO_MAX = timedelta(hours=12)


def _espera_audio(p: Post) -> bool:
    return p.tipo == "reel" and p.necesita_audio and bool(p.extra.get("contenido_aprobado"))


def pendientes(cola: list[Post], ahora: datetime) -> tuple[list[Post], list[Post]]:
    """(a_publicar, a_vencer) según la hora. Las reservas sólo salen reemplazando un reel sin audio."""
    a_publicar: list[Post] = []
    a_vencer: list[Post] = []
    reservas = [p for p in cola if p.reserva and p.estado == "aprobado"]
    for p in sorted(cola, key=lambda x: x.fecha_hora):
        if p.reserva or p.fecha_hora > ahora:
            continue
        atrasado = ahora - p.fecha_hora > ATRASO_MAX
        if p.estado == "aprobado":
            (a_vencer if atrasado else a_publicar).append(p)
        elif _espera_audio(p):
            if atrasado:
                a_vencer.append(p)
            elif reservas:
                a_publicar.append(reservas.pop(0))
                a_vencer.append(p)
    return a_publicar, a_vencer


def url_publica(post: Post, archivo: str, base: str) -> str:
    return f"{base.rstrip('/')}/cola/{post.id}/{archivo}"


class Meta:
    def __init__(self, ig_user_id: str, token: str, version: str = "v27.0"):
        self.ig = ig_user_id
        self.base = f"https://graph.facebook.com/{version}"
        self._s = requests.Session()
        self._s.headers["Authorization"] = f"Bearer {token}"  # header, así no aparece en URLs ni errores

    def _pedir(self, metodo: str, ruta: str, **kw) -> dict:
        r = self._s.request(metodo, f"{self.base}/{ruta}", timeout=60, **kw)
        try:
            datos = r.json()
        except ValueError:
            datos = {}
        if r.status_code >= 400 or "error" in datos:
            msg = (datos.get("error") or {}).get("message") or f"HTTP {r.status_code}"
            raise RuntimeError(f"Meta: {msg}")
        return datos

    def _crear(self, campos: dict) -> str:
        return self._pedir("POST", f"{self.ig}/media", data=campos)["id"]

    def crear_imagen(self, url: str, caption: str) -> str:
        return self._crear({"image_url": url, "caption": caption})

    def crear_carrusel(self, urls: list[str], caption: str) -> str:
        hijos = [self._crear({"image_url": u, "is_carousel_item": "true"}) for u in urls]
        return self._crear({"media_type": "CAROUSEL", "children": ",".join(hijos), "caption": caption})

    def crear_reel(self, url: str, caption: str) -> str:
        return self._crear({"media_type": "REELS", "video_url": url, "caption": caption, "share_to_feed": "true"})

    def esperar(self, container_id: str, intentos: int = 10, pausa_s: float = 30) -> None:
        for _ in range(intentos):
            datos = self._pedir("GET", container_id, params={"fields": "status_code,status"})
            estado = datos.get("status_code")
            if estado in ("FINISHED", "PUBLISHED"):
                return
            if estado in ("ERROR", "EXPIRED"):
                raise RuntimeError(f"contenedor {estado}: {datos.get('status', '')}")
            time.sleep(pausa_s)
        raise RuntimeError("el contenedor no terminó de procesarse a tiempo")

    def publicar(self, container_id: str) -> str:
        return self._pedir("POST", f"{self.ig}/media_publish", data={"creation_id": container_id})["id"]


def _publicar_uno(meta: Meta, p: Post, base_url: str) -> str:
    urls = [url_publica(p, a, base_url) for a in p.archivos]
    cap = caption(p)
    if p.tipo == "imagen":
        cid = meta.crear_imagen(urls[0], cap)
    elif p.tipo == "carrusel":
        cid = meta.crear_carrusel(urls, cap)
        meta.esperar(cid)
    else:
        cid = meta.crear_reel(urls[0], cap)
        meta.esperar(cid)
    return meta.publicar(cid)


def correr(
    raiz: Path,
    ahora: datetime,
    meta: Meta | None,
    base_url: str,
    al_guardar: Callable[[], None] | None = None,
) -> list[str]:
    al_guardar = al_guardar or (lambda: None)
    cola = cargar_cola(Path(raiz) / "cola")
    a_publicar, a_vencer = pendientes(cola, ahora)
    log: list[str] = []
    if meta is None:
        log.append("modo prueba: sin IG_USER_ID/IG_TOKEN, no se publica ni se cambia nada")
        log += [f"publicaría {p.id} ({p.tipo}, {p.fecha_hora:%d/%m %H:%M})" for p in a_publicar]
        log += [f"vencería {p.id}" for p in a_vencer]
        return log

    for p in a_vencer:
        p.estado = "vencido"
        p.error = "no salió a tiempo (más de 12 h de atraso o reel sin audio)"
        guardar_post(p)
        log.append(f"vencido {p.id}")

    for p in a_publicar:
        p.estado = "publicando"
        guardar_post(p)
        al_guardar()  # se sube este estado antes de publicar: evita doble publicación
        try:
            p.media_id = _publicar_uno(meta, p, base_url)
            p.estado, p.error = "publicado", None
            log.append(f"publicado {p.id} → {p.media_id}")
        except Exception as exc:  # noqa: BLE001 — cualquier falla queda registrada en la cola
            p.estado, p.error = "error", str(exc)
            log.append(f"ERROR {p.id}: {exc}")
        guardar_post(p)
    if not a_publicar and not a_vencer:
        log.append("nada para publicar")
    return log
