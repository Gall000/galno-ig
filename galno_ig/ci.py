"""Punto de entrada de GitHub Actions: python -m galno_ig.ci

Variables de entorno: IG_USER_ID, IG_TOKEN (secretos) y BASE_URL (URL de GitHub Pages).
Sin credenciales corre en modo prueba. Sale con código 1 si algo quedó en error,
así GitHub manda el mail de falla.
"""
from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from galno_ig.publicar import Meta, correr


def _subir_estado(raiz: Path, mensaje: str) -> None:
    subprocess.run(["git", "add", "cola"], cwd=raiz, check=True)
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=raiz).returncode == 0:
        return
    subprocess.run(["git", "commit", "-m", mensaje], cwd=raiz, check=True)
    subprocess.run(["git", "push"], cwd=raiz, check=True)


def main(raiz: Path = Path("."), subir: bool = True, ahora: datetime | None = None) -> int:
    raiz = Path(raiz)
    ig, token = os.environ.get("IG_USER_ID"), os.environ.get("IG_TOKEN")
    base = os.environ.get("BASE_URL", "")
    meta = Meta(ig, token) if ig and token else None
    if meta and not base:
        print("falta BASE_URL")
        return 1
    al_guardar = (lambda: _subir_estado(raiz, "estado: publicando")) if subir and meta else None
    log = correr(raiz, ahora or datetime.now(timezone.utc), meta, base, al_guardar=al_guardar)
    print("\n".join(log))
    if subir and meta:
        _subir_estado(raiz, "estado: publicaciones")
    hubo_error = meta is not None and any(l.startswith("ERROR") for l in log)
    return 1 if hubo_error else 0


if __name__ == "__main__":
    sys.exit(main())
