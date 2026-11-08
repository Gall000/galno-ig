"""Cola de publicaciones: cada publicación es una carpeta con un post.yaml."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal

import yaml

Tipo = Literal["imagen", "carrusel", "reel"]
Estado = Literal["borrador", "aprobado", "publicando", "publicado", "error", "vencido"]

AVISO_EJEMPLO = "Negocio de ejemplo"
HASHTAGS_MIN, HASHTAGS_MAX = 1, 3
CARRUSEL_MIN, CARRUSEL_MAX = 2, 20
MAX_IMAGEN = 8 * 1024 * 1024
MAX_VIDEO = 100 * 1024 * 1024  # límite duro de GitHub por archivo

# Campos que se guardan en post.yaml (id y carpeta salen del lugar en disco).
_CAMPOS = (
    "fecha_hora", "tipo", "archivos", "texto", "hashtags", "estado",
    "ejemplo", "reserva", "necesita_audio", "media_id", "error",
)


@dataclass
class Post:
    id: str
    carpeta: Path
    fecha_hora: datetime
    tipo: Tipo
    archivos: list[str]
    texto: str
    hashtags: list[str]
    estado: Estado
    ejemplo: bool = False
    reserva: bool = False
    necesita_audio: bool = False
    media_id: str | None = None
    error: str | None = None
    extra: dict = field(default_factory=dict)  # campos libres (p. ej. notas)


def cargar_post(carpeta: Path) -> Post:
    carpeta = Path(carpeta)
    datos = yaml.safe_load((carpeta / "post.yaml").read_text(encoding="utf-8")) or {}
    fh = datos.pop("fecha_hora")
    fecha_hora = fh if isinstance(fh, datetime) else datetime.fromisoformat(str(fh))
    if fecha_hora.tzinfo is None:
        raise ValueError(f"{carpeta.name}: fecha_hora sin zona horaria")
    conocidos = {k: datos.pop(k) for k in list(datos) if k in _CAMPOS}
    return Post(
        id=carpeta.name,
        carpeta=carpeta,
        fecha_hora=fecha_hora,
        tipo=conocidos["tipo"],
        archivos=[str(a) for a in conocidos.get("archivos", [])],
        texto=conocidos.get("texto", "") or "",
        hashtags=[str(h).lstrip("#") for h in conocidos.get("hashtags", []) or []],
        estado=conocidos.get("estado", "borrador"),
        ejemplo=bool(conocidos.get("ejemplo", False)),
        reserva=bool(conocidos.get("reserva", False)),
        necesita_audio=bool(conocidos.get("necesita_audio", False)),
        media_id=conocidos.get("media_id"),
        error=conocidos.get("error"),
        extra=datos,
    )


def guardar_post(post: Post) -> None:
    datos = {k: getattr(post, k) for k in _CAMPOS}
    datos["fecha_hora"] = post.fecha_hora.isoformat()
    datos.update(post.extra)
    texto = yaml.safe_dump(datos, allow_unicode=True, sort_keys=False, width=1000)
    (Path(post.carpeta) / "post.yaml").write_text(texto, encoding="utf-8")


def cargar_cola(raiz: Path, errores: list[str] | None = None) -> list[Post]:
    """Carga todas las carpetas con post.yaml. Una carpeta rota no frena a las demás:
    su problema se agrega a `errores` (si se pasa) o se relanza."""
    raiz = Path(raiz)
    posts = []
    for c in sorted(raiz.iterdir()):
        if not (c.is_dir() and (c / "post.yaml").exists()):
            continue
        try:
            posts.append(cargar_post(c))
        except Exception as exc:  # noqa: BLE001
            if errores is None:
                raise
            errores.append(f"{c.name}: post.yaml inválido ({exc!r})")
    return sorted(posts, key=lambda p: (p.fecha_hora, p.id))


def validar(post: Post) -> list[str]:
    problemas: list[str] = []
    if not HASHTAGS_MIN <= len(post.hashtags) <= HASHTAGS_MAX:
        problemas.append(f"hashtags: tiene {len(post.hashtags)}, van entre {HASHTAGS_MIN} y {HASHTAGS_MAX}")
    if not post.texto.strip():
        problemas.append("texto vacío")
    if post.ejemplo and AVISO_EJEMPLO.lower() not in post.texto.lower():
        problemas.append(f"muestra un negocio inventado y el texto no dice «{AVISO_EJEMPLO}»")
    if post.tipo not in ("imagen", "carrusel", "reel"):
        problemas.append(f"tipo desconocido: {post.tipo}")

    jpgs = [a for a in post.archivos if a.lower().endswith((".jpg", ".jpeg"))]
    mp4s = [a for a in post.archivos if a.lower().endswith(".mp4")]
    if post.tipo == "imagen" and (len(post.archivos) != 1 or len(jpgs) != 1):
        problemas.append("una imagen lleva exactamente un archivo .jpg")
    if post.tipo == "carrusel":
        if not CARRUSEL_MIN <= len(post.archivos) <= CARRUSEL_MAX:
            problemas.append(f"carrusel: tiene {len(post.archivos)} ítems, van entre {CARRUSEL_MIN} y {CARRUSEL_MAX}")
        if len(jpgs) != len(post.archivos):
            problemas.append("carrusel: todos los ítems tienen que ser .jpg")
    if post.tipo == "reel" and (len(post.archivos) != 1 or len(mp4s) != 1):
        problemas.append("un reel lleva exactamente un archivo .mp4")

    for a in post.archivos:
        ruta = Path(post.carpeta) / a
        if not ruta.exists():
            problemas.append(f"falta el archivo {a}")
            continue
        limite = MAX_VIDEO if a.lower().endswith(".mp4") else MAX_IMAGEN
        if ruta.stat().st_size > limite:
            problemas.append(f"{a} pesa más de {limite // (1024 * 1024)} MB")
    return problemas


def caption(post: Post) -> str:
    tags = " ".join(f"#{h}" for h in post.hashtags)
    return f"{post.texto.strip()}\n\n{tags}" if tags else post.texto.strip()
