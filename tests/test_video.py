import wave

import imageio_ffmpeg

from galno_ig.video import render_reel

DATOS = {
    "titulo": "¿Seguís tomando pedidos por audio?",
    "negocio": "Pizzería Ejemplo",
    "items": [{"nombre": "Muzzarella", "precio": "$ 9.500"}, {"nombre": "Napolitana", "precio": "$ 11.000"}],
    "ejemplo": True,
}


def _meta(ruta):
    gen = imageio_ffmpeg.read_frames(str(ruta))
    meta = next(gen)
    gen.close()
    return meta


def test_reel_mp4_dimensiones_y_duracion(tmp_path):
    salida = render_reel("reel-demo", DATOS, 4, tmp_path / "reel.mp4")
    meta = _meta(salida)
    assert tuple(meta["size"]) == (1080, 1920)
    assert 3.9 <= meta["duration"] <= 4.1


def test_reel_moov_al_principio(tmp_path):
    salida = render_reel("reel-demo", DATOS, 3, tmp_path / "reel.mp4", fps=10)
    cabeza = salida.read_bytes()[:65536]
    assert b"moov" in cabeza
    assert b"mdat" not in cabeza or cabeza.index(b"moov") < cabeza.index(b"mdat")


def test_reel_con_audio(tmp_path):
    wav = tmp_path / "silencio.wav"
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(44100)
        w.writeframes(b"\x00\x00" * 44100 * 4)
    salida = render_reel("reel-demo", DATOS, 4, tmp_path / "reel.mp4", audio=wav, fps=10)
    meta = _meta(salida)
    assert meta.get("audio_codec")
    assert 3.9 <= meta["duration"] <= 4.2
