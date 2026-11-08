"""Punto de entrada de GitHub Actions: python -m galno_ig.ci

Variables de entorno:
- IG_USER_ID, IG_TOKEN (secretos). Sin ellos corre en modo prueba.
- BASE_URL: URL de GitHub Pages del repo.
- FALLAR_SIN_CREDENCIALES=1: en modo prueba, falla si había algo para publicar
  (activarlo una vez conectado Meta, así un secreto vencido o borrado manda mail).

Sale con código 1 si algo quedó en error o vencido, así GitHub manda el mail de falla.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import requests

from galno_ig.publicar import Meta, correr


def _subir_estado(raiz: Path, mensaje: str, intentos: int = 3) -> None:
    subprocess.run(["git", "add", "cola"], cwd=raiz, check=True)
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=raiz).returncode != 0:
        subprocess.run(["git", "commit", "-m", mensaje], cwd=raiz, check=True)
    for i in range(intentos):
        # Si Lucas subió algo mientras corría, se trae primero (rebase) y se reintenta.
        subprocess.run(["git", "pull", "--rebase", "--quiet"], cwd=raiz, check=True)
        if subprocess.run(["git", "push", "--quiet"], cwd=raiz).returncode == 0:
            return
        time.sleep(5 * (i + 1))
    raise RuntimeError("no pude subir el estado al repositorio")


def _pages_tiene(url: str, tamanio: int) -> bool:
    """GitHub Pages ya sirve este archivo con este tamaño (deploy terminado, sin copia vieja)."""
    try:
        r = requests.head(url, allow_redirects=True, timeout=30)
    except requests.RequestException:
        return False
    return r.status_code == 200 and r.headers.get("Content-Length") == str(tamanio)


def main(
    raiz: Path = Path("."),
    subir: bool = True,
    ahora: datetime | None = None,
    verificar_url: Callable[[str, int], bool] | None = None,
) -> int:
    raiz = Path(raiz)
    ig, token = os.environ.get("IG_USER_ID"), os.environ.get("IG_TOKEN")
    base = os.environ.get("BASE_URL", "")
    meta = Meta(ig, token) if ig and token else None
    if meta and not base:
        print("falta BASE_URL")
        return 1
    al_guardar = (lambda: _subir_estado(raiz, "estado: publicando")) if subir and meta else None
    log = correr(raiz, ahora or datetime.now(timezone.utc), meta, base,
                 al_guardar=al_guardar, verificar_url=verificar_url or (_pages_tiene if meta else None))
    print("\n".join(log))
    if subir and meta:
        _subir_estado(raiz, "estado: publicaciones")
    if meta is None:
        pendiente = any(l.startswith("publicaría") for l in log)
        return 1 if pendiente and os.environ.get("FALLAR_SIN_CREDENCIALES") == "1" else 0
    malo = any(l.startswith("ERROR") or l.startswith("vencido") for l in log)
    return 1 if malo else 0


if __name__ == "__main__":
    sys.exit(main())
