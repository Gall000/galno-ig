"""Render de reels: plantilla HTML animada por tiempo → MP4 1080×1920 (H.264 + AAC)."""
from __future__ import annotations

import subprocess
from pathlib import Path

import imageio_ffmpeg

from galno_ig.render import html_de, pagina

ANCHO, ALTO = 1080, 1920


def render_reel(
    plantilla: str,
    datos: dict,
    duracion_s: float,
    salida: Path,
    audio: Path | None = None,
    fps: int = 30,
) -> Path:
    """Captura cuadro por cuadro llamando a window.__setTime(ms) y codifica con ffmpeg."""
    salida = Path(salida).resolve()
    salida.parent.mkdir(parents=True, exist_ok=True)
    duracion_ms = int(duracion_s * 1000)
    html = html_de(plantilla, {**datos, "duracion_ms": duracion_ms})
    tmp = salida.with_suffix(".tmp.html")
    tmp.write_text(html, encoding="utf-8")

    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error",
           "-f", "image2pipe", "-framerate", str(fps), "-i", "-"]
    if audio:
        cmd += ["-i", str(Path(audio).resolve())]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-profile:v", "high", "-preset", "medium", "-crf", "20",
            "-r", str(fps)]
    if audio:
        cmd += ["-c:a", "aac", "-b:a", "128k", "-ac", "2", "-af", "apad", "-t", f"{duracion_s:.3f}"]
    else:
        cmd += ["-an"]  # sólo para vistas previas: un reel sin audio nunca se aprueba
    cmd += ["-movflags", "+faststart", str(salida)]

    cuadros = round(duracion_s * fps)
    try:
        with pagina(ANCHO, ALTO) as page:
            page.goto(tmp.as_uri())
            page.wait_for_load_state("load")
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                for i in range(cuadros):
                    page.evaluate("t => window.__setTime(t)", i * 1000 / fps)
                    proc.stdin.write(page.screenshot(type="png"))
            finally:
                proc.stdin.close()
                err = proc.stderr.read().decode(errors="replace")
                if proc.wait() != 0:
                    raise RuntimeError(f"ffmpeg falló: {err}")
    finally:
        tmp.unlink(missing_ok=True)
    return salida
