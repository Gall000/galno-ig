"""Comandos: python -m galno_ig {semana|aprobar|audio|exportar} ..."""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

import yaml

from galno_ig.cola import cargar_cola, cargar_post, guardar_post
from galno_ig.semana import aprobar, exportar_business_suite, posts_de_semana, vista_html

RAIZ = Path(__file__).resolve().parent.parent
COLA = RAIZ / "cola"
SALIDA = RAIZ / "salida"


def _duracion_audio(ruta: Path) -> float:
    import imageio_ffmpeg

    r = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-i", str(ruta)], capture_output=True, text=True)
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r.stderr)
    if not m:
        raise ValueError(f"no pude leer la duración de {ruta}")
    h, mi, s = m.groups()
    return int(h) * 3600 + int(mi) * 60 + float(s)


def cmd_semana(a):
    lunes = date.fromisoformat(a.lunes)
    cola = cargar_cola(COLA)
    semana = posts_de_semana(cola, lunes)
    reservas = [p for p in cola if p.reserva and p not in semana and p.estado in ("borrador", "aprobado")]
    print(vista_html(semana + reservas, SALIDA / f"semana-{lunes}.html"))


def cmd_aprobar(a):
    ok = True
    for id in a.ids:
        p = cargar_post(COLA / id)
        try:
            aprobar(p)
            print(f"{id}: {'contenido aprobado, falta audio' if p.necesita_audio else 'aprobado'}")
        except ValueError as e:
            ok = False
            print(f"NO aprobado → {e}")
    sys.exit(0 if ok else 1)


def cmd_audio(a):
    """Copia el audio a la carpeta del reel, re-renderiza con voz y lo deja listo para salir."""
    from galno_ig.video import render_reel

    p = cargar_post(COLA / a.id)
    if p.tipo != "reel":
        sys.exit(f"{a.id} no es un reel")
    spec = yaml.safe_load((p.carpeta / "reel.yaml").read_text(encoding="utf-8"))
    origen = Path(a.archivo)
    voz = p.carpeta / f"voz{origen.suffix.lower()}"
    shutil.copy2(origen, voz)
    duracion = max(float(spec["duracion_s"]), _duracion_audio(voz) + 2.5)  # +2,5 s de cierre
    render_reel(spec["plantilla"], spec.get("datos", {}), duracion, p.carpeta / p.archivos[0], audio=voz)
    p.necesita_audio = False
    if p.extra.pop("contenido_aprobado", False):
        p.estado = "aprobado"
    guardar_post(p)
    print(f"{a.id}: reel con voz ({duracion:.1f} s), estado {p.estado}")


def cmd_exportar(a):
    lunes = date.fromisoformat(a.lunes)
    posts = [p for p in posts_de_semana(cargar_cola(COLA), lunes) if p.estado == "aprobado"]
    print(exportar_business_suite(posts, SALIDA / f"business-suite-{lunes}"))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="galno_ig")
    sub = ap.add_subparsers(required=True)
    s = sub.add_parser("semana", help="genera la vista de la semana para aprobar")
    s.add_argument("lunes")
    s.set_defaults(f=cmd_semana)
    s = sub.add_parser("aprobar", help="aprueba publicaciones por id")
    s.add_argument("ids", nargs="+")
    s.set_defaults(f=cmd_aprobar)
    s = sub.add_parser("audio", help="carga la voz de un reel y lo re-renderiza")
    s.add_argument("id")
    s.add_argument("archivo")
    s.set_defaults(f=cmd_audio)
    s = sub.add_parser("exportar", help="exporta lo aprobado de la semana para Business Suite")
    s.add_argument("lunes")
    s.set_defaults(f=cmd_exportar)
    a = ap.parse_args(argv)
    a.f(a)


if __name__ == "__main__":
    main()
