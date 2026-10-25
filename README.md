# Hub de aplicaciones

La aplicación usa `app.py` como punto de entrada y organiza sus funciones en
módulos independientes. El hub vive en `app_pages/home.py`; cada módulo mantiene
sus páginas dentro de `modules/<modulo>/views/`.

## Módulos actuales

- **Gestión**: dashboard, pedidos, productos e inventario, clientes y usuarios.
- **Reloj PDF**: genera un PDF descargable con la fecha y hora de Bogotá.
- **QR Generator**: QR para texto, URL y redes Wi-Fi.
- **JSON Formatter**: validación, formato y minificación JSON.
- **PDF Toolbox**: unir/dividir PDF, PDF a DOCX y DOCX a PDF cuando LibreOffice esté instalado.

## Inicio de sesión y permisos

El acceso se administra en la tabla `app_access_users` de Supabase, sin
depender de Supabase Auth ni OIDC. Las contraseñas nunca se guardan en texto
plano: se almacenan como hash PBKDF2-HMAC-SHA256.

1. Aplica las migraciones actuales en orden: `20261025010000_cuentas_acceso.sql`
   si aún no existe `app_access_users`, y `20261025020000_catalogo_apps.sql`
   para el catálogo. La antigua migración `20261025000000_accesos_modulos.sql`
   ya no forma parte del sistema.
2. Configura el correo del superadministrador y una contraseña inicial segura
   en `.streamlit/secrets.toml`:

```toml
[supabase]
url = "https://tu-proyecto.supabase.co"
key = "tu-clave-service-role"

[bootstrap]
super_admin_email = "edwin.torres.r2000@gmail.com"
super_admin_password = "reemplaza-por-una-clave-aleatoria-de-12-o-mas-caracteres"
```

Al iniciar la app por primera vez con la tabla vacía, se crea en Supabase el
registro de superadministrador y se guarda únicamente el hash de la contraseña.
Inicia sesión para comprobarlo y luego elimina `super_admin_password` de
`secrets.toml`. Para una cuenta creada manualmente mediante SQL, `password_hash`
debe usar el formato PBKDF2-HMAC-SHA256 que verifica `services/access_control.py`;
no guardes la contraseña en texto plano. Los siguientes usuarios y sus
aplicaciones se administran desde **Gestión → Usuarios y roles**. Las cuentas
nuevas o actualizadas desde la interfaz requieren contraseñas de al menos 12
caracteres. Si usas una contraseña temporal débil para el primer inicio,
cámbiala inmediatamente desde la administración.

Las tablas habilitan RLS sin políticas públicas; la aplicación las consulta
desde el servidor. Usa una clave privada `service_role` en `secrets.toml`;
nunca la expongas en código, en el navegador ni en el repositorio.

## Catálogo y permisos por aplicación

El catálogo se define en el registro `APP_MODULES` y se sincroniza con
`app_catalog` mediante la migración idempotente. Desde **Gestión → Usuarios y
roles**, el superadministrador puede activar/desactivar las apps y asignar a
cada cuenta individualmente las activas. Los usuarios normales no reciben
permisos nuevos por defecto. Cada página vuelve a comprobar en Supabase que la
cuenta esté activa, que la app siga habilitada y que el módulo esté asignado;
ocultar la navegación no es el único control.

## Nuevas aplicaciones

### QR Generator

Genera PNG de URL/texto o Wi-Fi con corrección de errores seleccionable. La
contraseña Wi-Fi se procesa solo en memoria y no se almacena. Dependencia:
`qrcode[pil]` (BSD-3-Clause), Pillow (HPND).

### JSON Formatter

Valida, indenta, minifica y descarga JSON en memoria usando el módulo estándar
`json` de Python. No añade dependencias externas; límite de entrada: 2 MB.

### PDF Toolbox

Une PDF ordenados, extrae páginas por rangos y extrae texto de PDF a DOCX. PDF
escaneados sin texto seleccionable requieren OCR (no incluido); la conversión a
Word no conserva el diseño original. DOCX a PDF requiere LibreOffice Writer en
el servidor; si no está instalado, se informa en pantalla. Los archivos se
limitan a 20 MB por archivo, 20 archivos y 40 MB en total al unir, 500 páginas
y se procesan en memoria, salvo el directorio temporal aislado y eliminado por
LibreOffice.

Dependencias nuevas: `pypdf` (BSD-3-Clause) para PDF y `python-docx` (MIT) para
DOCX. Se evita `pdf2docx`/PyMuPDF para no introducir su carga de licencia
AGPL/comercial; PDF a Word ofrece extracción de texto básica, no una conversión
fiel de diseño.

Instala dependencias y ejecuta desde la raíz:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Para Word a PDF en Debian/Ubuntu: `sudo apt install libreoffice-writer`.

## Agregar otro módulo

1. Crea `modules/<nombre>/` y coloca sus páginas dentro de `views/`.
2. Declara en `modules/<nombre>/__init__.py` un diccionario `MODULE` con
   `title`, `description`, `icon`, `entrypoint` y la lista `pages`.
3. Asegúrate de incluir en cada módulo un `id` único, `entrypoint` y sus páginas.
4. Importa ese `MODULE` en `modules/__init__.py` y agrégalo a `APP_MODULES`.

El hub crea automáticamente una tarjeta para cada módulo y `app.py` incorpora
sus páginas a la navegación. El nuevo módulo aparecerá en el selector de
permisos por usuario.
