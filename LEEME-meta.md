# Conectar la publicación automática con Meta

Mientras esto no esté, se usa el plan B: `python -m galno_ig exportar <lunes>` y se programa a mano en Meta Business Suite.

1. **Cuenta profesional** de Instagram de Galno Assist (empresa o creador) **vinculada a la página de Facebook** de Galno Assist. En la página, tu usuario necesita control total o la tarea «Contenido». La página no puede exigir *Page Publishing Authorization* pendiente.
2. **App de Meta**: la misma de Sherlock. Agregar el producto Instagram (API con inicio de sesión de Facebook). Vos tenés que tener rol en la app (admin). Con **acceso estándar** alcanza: la app sólo publica en tu propia cuenta, no hace falta revisión de Meta.
3. **Permisos** del token: `instagram_basic`, `instagram_content_publish`, `pages_read_engagement` (Sherlock usa además los de Business Discovery).
4. **Token**: en el Explorador de la Graph API generar un token de usuario con esos permisos → cambiarlo por uno de larga duración → pedir `/me/accounts` y tomar el **token de la página**. Revisar en el *Depurador de tokens* cuándo vence (los de página sacados de un token largo suelen no vencer; si vence, anotar la fecha para renovarlo).
5. **IG_USER_ID**: `GET /{page-id}?fields=instagram_business_account` → el `id`.
6. **GitHub** (repo `galno-ig` → Settings):
   - *Secrets and variables → Actions → Secrets*: `IG_USER_ID` y `IG_TOKEN`.
   - *Variables*: `BASE_URL` = `https://gall000.github.io/galno-ig`.
   - *Pages*: rama `main`, carpeta `/`.
7. Probar con *Actions → publicar → Run workflow* y una publicación de prueba aprobada.

Si una ejecución falla, GitHub te manda un mail y la publicación queda en `estado: error` con el motivo. Para reintentarla, volver a ponerla en `aprobado` (y ajustar la fecha si pasaron más de 12 h).

Nota: GitHub desactiva los workflows programados de repos públicos tras 60 días sin commits; los commits de estado y de cada semana lo mantienen activo.
