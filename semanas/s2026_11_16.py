"""Primera semana: 16 al 22 de noviembre de 2026 (+ 2 reservas).

Correr:  .venv/Scripts/python -m semanas.s2026_11_16
Crea/actualiza cola/<id>/ con post.yaml, imágenes y reels de vista previa (sin voz).
No pisa el estado de una publicación que ya no esté en borrador.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

from galno_ig.cola import Post, cargar_post, guardar_post
from galno_ig.render import render_carrusel, render_imagen
from galno_ig.video import render_reel

AR = timezone(timedelta(hours=-3))
COLA = Path(__file__).resolve().parent.parent / "cola"
CTA = "Escribime por DM"


def fh(dia: int, hora: int, minuto: int = 0) -> datetime:
    return datetime(2026, 11, dia, hora, minuto, tzinfo=AR)


def cierre(titulo: str, bajada: str = "Si te sirvió, guardalo o mandáselo a alguien que tenga un local.") -> dict:
    return {"etiqueta": "Para guardar", "titulo": titulo, "cuerpo": bajada + " " + CTA + ".", "fondo": "oscuro"}


CARRUSELES = {
    "2026-11-16-lun-senales-whatsapp": dict(
        fecha_hora=fh(16, 8, 30),
        hashtags=["negocioslocales", "whatsappbusiness", "emprendedores"],
        texto=(
            "Si tu local vende por WhatsApp, estas 3 señales te dicen que se te están yendo pedidos.\n\n"
            "Ninguna se arregla trabajando más horas: se arreglan dejando a la vista lo que el cliente pregunta siempre.\n\n"
            f"¿Te pasa alguna? {CTA} y te digo cómo lo resolvería en tu caso."
        ),
        slides=[
            {"etiqueta": "Consejo", "titulo": "3 señales de que perdés pedidos por WhatsApp"},
            {"etiqueta": "Señal 1", "titulo": "Respondés lo mismo diez veces por día",
             "cuerpo": "Precio, horario, si hay stock. Cada pregunta repetida es un cliente esperando una respuesta que podría leer solo."},
            {"etiqueta": "Señal 2", "titulo": "Los pedidos llegan en audios",
             "cuerpo": "Hay que escucharlos, anotarlos y confirmar. Un error en un audio es un pedido mal hecho o un cliente que no vuelve."},
            {"etiqueta": "Señal 3", "titulo": "Contestás tarde porque estás atendiendo",
             "cuerpo": "El que pregunta a las 21 y recibe respuesta a las 23 ya pidió en otro lado."},
            {"etiqueta": "Qué hacer", "titulo": "Que el cliente se responda solo",
             "items": ["Carta o lista con precios a un link", "Pedido armado antes de escribirte", "Horarios y zona de envío a la vista"]},
            {"etiqueta": "El resultado", "titulo": "Menos mensajes, pedidos más claros",
             "cuerpo": "Te llega el pedido completo, por escrito, listo para preparar. Vos seguís usando WhatsApp, pero trabaja para vos."},
            cierre("Revisá estas 3 señales esta semana"),
        ],
    ),
    "2026-11-20-vie-errores-carta": dict(
        fecha_hora=fh(20, 12, 30),
        hashtags=["gastronomia", "cartadigital", "negocioslocales"],
        texto=(
            "La carta digital no es subir una foto del menú impreso.\n\n"
            "Estos son los 5 errores que más veo en bares, pizzerías y cafeterías. Si tu carta tiene 2 o más, el cliente se va antes de pedir.\n\n"
            f"{CTA} si querés que mire la tuya."
        ),
        slides=[
            {"etiqueta": "Gastronomía", "titulo": "5 errores de la carta digital de tu local"},
            {"etiqueta": "Error 1", "titulo": "Es una foto o un PDF",
             "cuerpo": "En el celular hay que hacer zoom para leer. Nadie hace zoom con hambre."},
            {"etiqueta": "Error 2", "titulo": "Precios viejos",
             "cuerpo": "Si el precio no coincide, el cliente desconfía de todo lo demás. Tiene que poder actualizarse en un minuto."},
            {"etiqueta": "Error 3", "titulo": "No dice cómo pedir",
             "cuerpo": "La carta termina y no hay un botón. El cliente tiene que buscar tu número y escribir desde cero."},
            {"etiqueta": "Error 4", "titulo": "Todo en una sola lista",
             "cuerpo": "Sin categorías, el cliente scrollea y no encuentra. Entradas, principales, bebidas, postres: arriba y fáciles de tocar."},
            {"etiqueta": "Error 5", "titulo": "No está en tu bio",
             "cuerpo": "Si la carta está bien pero nadie la encuentra, no existe. El link va en Instagram, en Google y en el QR de la mesa."},
            cierre("¿Cuántos tiene tu carta?"),
        ],
    ),
    "2026-11-22-dom-servicio-turnos": dict(
        fecha_hora=fh(22, 11),
        hashtags=["turnosonline", "barberia", "negocioslocales"],
        texto=(
            "Servicio de la semana: turnos online.\n\n"
            "Para barberías, peluquerías, centros de estética, talleres y consultorios: el cliente ve los horarios libres y reserva solo, "
            "sin ida y vuelta de mensajes.\n\n"
            f"{CTA} y te muestro cómo quedaría con tus horarios."
        ),
        slides=[
            {"etiqueta": "Servicio de la semana", "titulo": "Turnos online"},
            {"etiqueta": "Qué es", "titulo": "Una página con tus horarios libres",
             "cuerpo": "El cliente elige el servicio, el día y la hora. El turno queda anotado y a vos te llega el aviso."},
            {"etiqueta": "Para quién", "titulo": "Si trabajás con agenda",
             "items": ["Barberías y peluquerías", "Estética y uñas", "Talleres mecánicos", "Consultorios y clases"]},
            {"etiqueta": "Qué cambia", "titulo": "Se terminan los «¿tenés lugar el sábado?»",
             "cuerpo": "Menos mensajes mientras atendés, menos turnos cruzados y menos huecos en la agenda."},
            {"etiqueta": "Cómo se usa", "titulo": "Un link en tu bio y en WhatsApp",
             "cuerpo": "No hace falta que el cliente baje una app ni cree una cuenta."},
            {"etiqueta": "Lo que necesito de vos", "titulo": "Tus servicios, tus horarios y cuánto dura cada uno",
             "cuerpo": "Con eso lo armo y te lo muestro funcionando antes de que decidas nada."},
            cierre("¿Tu negocio trabaja con turnos?", "Guardalo para cuando lo pienses, o mandáselo a quien le sirva."),
        ],
    ),
    "reserva-bio-instagram": dict(
        fecha_hora=fh(23, 8, 30), reserva=True,
        hashtags=["negocioslocales", "instagramparanegocios"],
        texto=(
            "Tu bio de Instagram es lo primero que lee un cliente nuevo. En pocas líneas tiene que contestar 4 cosas.\n\n"
            f"Si la tuya no las contesta, {CTA.lower()} y la revisamos."
        ),
        slides=[
            {"etiqueta": "Consejo", "titulo": "4 cosas que tu bio tiene que decir"},
            {"etiqueta": "1", "titulo": "Qué hacés", "cuerpo": "En palabras de cliente: «Pizzas a la piedra con envío», no «Pasión por la gastronomía»."},
            {"etiqueta": "2", "titulo": "Dónde estás", "cuerpo": "Barrio o zona de envío. El que es de otra zona se ahorra preguntar."},
            {"etiqueta": "3", "titulo": "Cuándo atendés", "cuerpo": "Días y horario. Si cambia seguido, que el link lo muestre actualizado."},
            {"etiqueta": "4", "titulo": "Cómo te compran", "cuerpo": "Un solo link claro: carta, catálogo o turnos. No cinco links distintos."},
            {"etiqueta": "Ejemplo", "titulo": "Pizzería · tu barrio", "cuerpo": "A la piedra, con envío en la zona. Mar a dom, de 19 a 24. Pedí acá ↓"},
            cierre("Revisá tu bio hoy"),
        ],
    ),
}

PLACAS = {
    "2026-11-21-sab-idea-llamar": dict(
        fecha_hora=fh(21, 11),
        hashtags=["negocioslocales", "comerciolocal"],
        texto=(
            "Cada vez más clientes prefieren no llamar ni preguntar: quieren ver el precio, elegir y pedir.\n\n"
            f"Si tu negocio todavía depende de que te escriban para saber qué hay, {CTA.lower()}."
        ),
        datos={"etiqueta": "Idea", "titulo": "Tu cliente no quiere llamarte.", "bajada": "Quiere ver el precio y pedir.", "fondo": "oscuro"},
    ),
    "reserva-horario-destacada": dict(
        fecha_hora=fh(23, 11), reserva=True,
        hashtags=["negocioslocales", "comerciolocal"],
        texto=(
            "Las historias destacadas no las abre casi nadie. Horario, precios y cómo pedir tienen que estar a un toque, "
            f"en la bio o en un link.\n\n{CTA} si querés ordenarlo."
        ),
        datos={"etiqueta": "Idea", "titulo": "Si tu horario está en una historia destacada,", "bajada": "para muchos clientes no existe.", "fondo": "claro"},
    ),
}

# Subtítulos: frases clave sincronizadas con la animación (la voz sigue el guion al mismo ritmo).
REELS = {
    "2026-11-17-mar-demo-pedidos": dict(
        fecha_hora=fh(17, 20), ejemplo=True,
        hashtags=["pizzeria", "pedidosonline", "gastronomia"],
        texto=(
            "Negocio de ejemplo: así pide un cliente en una pizzería sin mandar un audio.\n\n"
            "Ve la carta con precios, arma el pedido y te llega por WhatsApp completo y por escrito. Vos lo preparás, sin anotar nada.\n\n"
            f"Sirve para pizzerías, rotiserías, heladerías y cualquier local que tome pedidos. {CTA}."
        ),
        plantilla="reel-demo", duracion_s=26,
        datos={
            "titulo": "¿Seguís tomando pedidos por audio?",
            "negocio": "Pizzería Ejemplo",
            "items": [{"nombre": "Muzzarella", "precio": "$ 9.500"}, {"nombre": "Napolitana", "precio": "$ 11.000"},
                      {"nombre": "Fugazzeta", "precio": "$ 10.800"}, {"nombre": "Empanadas x6", "precio": "$ 8.400"}],
            "cierre_titulo": "Pedidos claros, sin audios.",
            "cierre_bajada": "Escribime por DM y lo armamos para tu local.",
            "subtitulos": [
                {"desde_ms": 0, "hasta_ms": 3500, "texto": "Así pide un cliente sin mandarte un audio"},
                {"desde_ms": 3500, "hasta_ms": 9500, "texto": "Ve la carta con precios actualizados"},
                {"desde_ms": 9500, "hasta_ms": 16500, "texto": "Arma el pedido tocando +"},
                {"desde_ms": 16500, "hasta_ms": 23500, "texto": "Y te llega completo por WhatsApp"},
            ],
        },
        guion=(
            "[0-3 s] ¿Seguís tomando pedidos por audio? Mirá cómo pide un cliente en esta pizzería, que es un ejemplo.\n"
            "[3-9 s] Entra al link, ve la carta con los precios de hoy.\n"
            "[9-16 s] Toca más en lo que quiere: una muzza, una napo, una docena de empanadas.\n"
            "[16-23 s] Y toca «Pedir por WhatsApp». A vos te llega el pedido completo, escrito, listo para preparar.\n"
            "[23-26 s] Si tu local toma pedidos, escribime por DM y lo armamos con tu carta."
        ),
    ),
    "2026-11-18-mie-antes-despues-turnos": dict(
        fecha_hora=fh(18, 20), ejemplo=True,
        hashtags=["barberia", "turnosonline", "emprendedores"],
        texto=(
            "Negocio de ejemplo: una barbería antes y después de tener turnos online.\n\n"
            "Antes: diez mensajes para encontrar un horario, mientras estás cortando. Después: el cliente ve lo libre y reserva solo.\n\n"
            f"{CTA} si querés verlo con tus horarios."
        ),
        plantilla="reel-antes-despues", duracion_s=26,
        datos={
            "titulo": "Diez mensajes para sacar un turno",
            "negocio": "Barbería Ejemplo",
            "antes": [
                {"texto": "Hola! Tenés lugar el sábado?", "yo": False},
                {"texto": "Hola! A qué hora te queda bien?", "yo": True},
                {"texto": "A la tarde, tipo 4?", "yo": False},
                {"texto": "A las 4 no, tengo 17:30", "yo": True},
                {"texto": "Uh, y a la mañana?", "yo": False},
            ],
            "despues_titulo": "Sábado 21 · Corte",
            "turnos": [{"hora": "10:00", "estado": "tomado"}, {"hora": "11:00", "estado": "libre"},
                       {"hora": "16:00", "estado": "tomado"}, {"hora": "17:30", "estado": "libre"},
                       {"hora": "18:30", "estado": "libre"}],
            "elegido": 1,
            "confirmacion": "Turno confirmado · Sáb 11:00",
            "cierre_titulo": "Tu agenda se llena sola.",
            "cierre_bajada": "Escribime por DM y la armamos con tus horarios.",
            "subtitulos": [
                {"desde_ms": 0, "hasta_ms": 10500, "texto": "Antes: ida y vuelta mientras estás atendiendo"},
                {"desde_ms": 10500, "hasta_ms": 17000, "texto": "Después: el cliente ve los horarios libres"},
                {"desde_ms": 17000, "hasta_ms": 23500, "texto": "Elige uno y queda confirmado"},
            ],
        },
        guion=(
            "[0-3 s] Diez mensajes para sacar un turno. Esto pasa en una barbería de ejemplo.\n"
            "[3-10 s] «¿Tenés lugar el sábado?» «¿A qué hora?» «¿Tipo cuatro?» «No, tengo cinco y media»… y vos con la máquina en la mano.\n"
            "[10-17 s] Ahora, con turnos online: el cliente abre el link y ve qué horarios están libres.\n"
            "[17-23 s] Toca el de las once, y listo, queda confirmado. A vos te llega el aviso.\n"
            "[23-26 s] Si trabajás con turnos, escribime por DM y lo armamos con tu agenda."
        ),
    ),
    "2026-11-19-jue-caso-desdechile": dict(
        fecha_hora=fh(19, 20), ejemplo=False,
        hashtags=["emprendedores", "catalogoonline"],
        texto=(
            "Antes de Galno Assist tuve un emprendimiento: DesdeChile.Ar, productos traídos de Chile.\n\n"
            "Los reels funcionaban, pero cada venta empezaba con «¿qué hay disponible?» por mensaje. Le faltaba lo más simple: "
            "un catálogo con lo disponible y un botón para pedir.\n\n"
            f"Hoy eso es lo que armo para otros emprendimientos. {CTA}."
        ),
        plantilla="reel-demo", duracion_s=28,
        datos={
            "titulo": "Lo que le faltaba a mi emprendimiento",
            "negocio": "DesdeChile.Ar",
            # CONFIRMAR con Lucas: productos y precios reales de DesdeChile.Ar.
            "items": [{"nombre": "Camiseta (talle M)", "precio": "$ —"}, {"nombre": "Camiseta (talle L)", "precio": "$ —"},
                      {"nombre": "Producto 3", "precio": "$ —"}],
            "cierre_titulo": "Un catálogo y un botón para pedir.",
            "cierre_bajada": "Escribime por DM si vendés por Instagram.",
            "subtitulos": [
                {"desde_ms": 0, "hasta_ms": 5000, "texto": "Tuve un emprendimiento: DesdeChile.Ar"},
                {"desde_ms": 5000, "hasta_ms": 12000, "texto": "Cada venta empezaba con «¿qué hay disponible?»"},
                {"desde_ms": 12000, "hasta_ms": 19000, "texto": "Le faltaba un catálogo con lo disponible"},
                {"desde_ms": 19000, "hasta_ms": 25500, "texto": "Y un botón para pedir"},
            ],
        },
        guion=(
            "[0-5 s] Te muestro lo que le faltaba a mi propio emprendimiento. Se llamaba DesdeChile.Ar: traíamos productos de Chile.\n"
            "[5-12 s] Los reels andaban bien, pero cada venta arrancaba igual: «¿qué hay disponible?», por mensaje, una y otra vez.\n"
            "[12-19 s] Hoy lo resolvería así: un catálogo con lo que hay, con precio y talle.\n"
            "[19-25 s] Y un botón para pedir por WhatsApp. El cliente llega sabiendo qué quiere.\n"
            "[25-28 s] Eso armo ahora para otros emprendimientos. Escribime por DM.\n\n"
            "ANTES DE APROBAR: confirmar productos y precios reales de DesdeChile.Ar (hoy son marcadores)."
        ),
    ),
}


def _preparar(id: str, tipo: str, archivos: list[str], spec: dict, necesita_audio: bool = False) -> Post | None:
    carpeta = COLA / id
    if (carpeta / "post.yaml").exists() and cargar_post(carpeta).estado != "borrador":
        print(f"{id}: ya no está en borrador, no se toca")
        return None
    carpeta.mkdir(parents=True, exist_ok=True)
    return Post(
        id=id, carpeta=carpeta, fecha_hora=spec["fecha_hora"], tipo=tipo, archivos=archivos,
        texto=spec["texto"], hashtags=spec["hashtags"], estado="borrador",
        ejemplo=spec.get("ejemplo", False), reserva=spec.get("reserva", False), necesita_audio=necesita_audio,
    )


def main() -> None:
    for id, spec in CARRUSELES.items():
        archivos = [f"{i:02d}.jpg" for i in range(1, len(spec["slides"]) + 1)]
        if p := _preparar(id, "carrusel", archivos, spec):
            render_carrusel(spec["slides"], p.carpeta)
            guardar_post(p)
            print(f"{id}: carrusel de {len(archivos)}")
    for id, spec in PLACAS.items():
        if p := _preparar(id, "imagen", ["01.jpg"], spec):
            render_imagen("placa", {**spec["datos"], "ejemplo": spec.get("ejemplo", False)}, p.carpeta / "01.jpg")
            guardar_post(p)
            print(f"{id}: placa")
    for id, spec in REELS.items():
        if p := _preparar(id, "reel", ["reel.mp4"], spec, necesita_audio=True):
            datos = {**spec["datos"], "ejemplo": spec.get("ejemplo", False)}
            (p.carpeta / "reel.yaml").write_text(
                yaml.safe_dump({"plantilla": spec["plantilla"], "duracion_s": spec["duracion_s"], "datos": datos},
                               allow_unicode=True, sort_keys=False), encoding="utf-8")
            (p.carpeta / "guion.md").write_text(f"# Guion · {id}\n\n{spec['guion']}\n", encoding="utf-8")
            render_reel(spec["plantilla"], datos, spec["duracion_s"], p.carpeta / "reel.mp4")
            guardar_post(p)
            print(f"{id}: reel de vista previa (sin voz)")


if __name__ == "__main__":
    main()
