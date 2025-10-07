# Instrucciones Adicionales - Gestor de Inversiones

## Configuración de Supabase

### 1. Crear Proyecto en Supabase

1. Ve a [https://supabase.com](https://supabase.com)
2. Crea una cuenta o inicia sesión
3. Crea un nuevo proyecto
4. Espera a que se complete la configuración (2-3 minutos)

### 2. Configurar Base de Datos

1. En tu proyecto de Supabase, ve a la sección **SQL Editor**
2. Copia y pega todo el contenido del archivo `database_setup.sql`
3. Ejecuta el script haciendo clic en **Run**
4. Verifica que se crearon las tablas `users` e `investments`

### 3. Obtener Credenciales

1. Ve a **Settings** > **API**
2. Copia la **URL** del proyecto
3. Copia la **anon public** key
4. Copia la **service_role** key (mantener secreta)

### 4. Configurar Authentication

**Crear usuarios desde el panel de Supabase:**

1. Ve a **Authentication** > **Users**
2. Haz clic en **Add user**
3. Ingresa:
   - Email del usuario
   - Contraseña temporal
   - Confirma si quieres que el email sea verificado automáticamente
4. El usuario podrá iniciar sesión con estas credenciales

**Configuración opcional de Authentication:**

1. Ve a **Authentication** > **Settings**
2. Configura opciones como:
   - Confirmación de email requerida
   - Políticas de contraseña
   - URLs de redirection
   - Proveedores adicionales (Google, GitHub, etc.)

### 5. Configurar Políticas de Seguridad

Las políticas RLS ya están incluidas en el script SQL, pero puedes verificarlas:

1. Ve a **Authentication** > **Policies**
2. Verifica que existan políticas para la tabla `investments`
3. Las políticas aseguran que cada usuario solo vea sus propias inversiones

## Gestión de Usuarios

### Crear Nuevos Usuarios

**Desde el panel de Supabase:**

1. Ve a tu proyecto en [https://supabase.com](https://supabase.com)
2. Navega a **Authentication** > **Users**
3. Haz clic en **Add user**
4. Completa el formulario:
   ```
   Email: usuario@ejemplo.com
   Password: contraseña_segura
   Email Confirm: true (si quieres verificación automática)
   ```
5. Haz clic en **Create user**

### Gestionar Usuarios Existentes

**Acciones disponibles:**
- Ver lista de todos los usuarios
- Editar información de usuario
- Cambiar contraseñas
- Suspender/reactivar usuarios
- Ver sesiones activas
- Eliminar usuarios

### Verificación de Email

**Configurar verificación automática:**
1. Ve a **Authentication** > **Settings**
2. En **User Signups**, configura:
   - Enable email confirmations: `Enabled`
   - Enable phone confirmations: `Disabled` (opcional)

### Recuperación de Contraseña

Los usuarios pueden recuperar contraseñas automáticamente si tienes configurado:
1. **Authentication** > **Settings** > **Password Recovery**
2. Asegúrate de que esté habilitado
3. Configura las plantillas de email si es necesario

## Datos de Ejemplo

Una vez que tengas la aplicación funcionando y usuarios creados en Supabase, puedes crear inversiones de ejemplo:

### Usuario de Prueba
**Crear desde Supabase Auth:**
- Email: `admin@ejemplo.com`
- Password: `password123`

### Plazo Fijo
- **Nombre**: Plazo Fijo Banco Nación 90 días
- **Organismo**: Banco Nación
- **Tipo**: plazo fijo
- **Estado**: activa
- **Monto**: 500,000 ARS
- **Tasa**: 75% anual
- **Fecha inicio**: Hoy
- **Fecha fin**: +90 días

### Bonos
- **Nombre**: Bonos AL30
- **Organismo**: Invertir Online
- **Tipo**: bonos
- **Estado**: activa
- **Monto**: 10,000 USD
- **Tasa**: 15% anual
- **Fecha inicio**: Hoy
- **Fecha fin**: +365 días

### FCI
- **Nombre**: FCI Renta Variable
- **Organismo**: Balanz
- **Tipo**: fondo comun
- **Estado**: en estudio
- **Monto**: 200,000 ARS
- **Sin tasa (variable)

**Nota:** Las inversiones se crean desde la aplicación web una vez que el usuario esté autenticado.

## Comandos Útiles

### Activar entorno virtual
```bash
# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### Instalar nueva dependencia
```bash
pip install nombre_paquete
pip freeze > requirements.txt
```

### Ejecutar aplicación en modo debug
```bash
export FLASK_ENV=development  # Linux/macOS
set FLASK_ENV=development     # Windows
python app.py
```

### Ver logs de Supabase
En el dashboard de Supabase, ve a **Logs** para ver queries y errores.

## Personalización Avanzada

### Agregar nuevos campos a inversiones

1. Modificar la tabla en Supabase:
```sql
ALTER TABLE investments ADD COLUMN nuevo_campo VARCHAR(100);
```

2. Actualizar `models.py` para incluir el nuevo campo
3. Modificar los templates para mostrar/editar el campo

### Cambiar colores del tema

Editar las variables CSS en `static/css/style.css`:
```css
:root {
    --primary-color: #tu_color;
    --success-color: #tu_color;
    /* etc */
}
```

### Agregar nuevos tipos de cálculo

Modificar el método `calculate_estimated_return()` en `models.py`.

## Solución de Problemas Comunes

### Error "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

### Error de conexión a Supabase
- Verificar credenciales en `.env`
- Verificar que las tablas existan
- Revisar logs en dashboard de Supabase

### Error de permisos en base de datos
- Verificar que RLS esté configurado
- Revisar las políticas de seguridad

### La aplicación no muestra datos
- Verificar que las políticas RLS permitan acceso
- Revisar la consola del navegador para errores
- Verificar que los datos se estén insertando correctamente

## Optimización para Producción

### Variables de entorno
```env
FLASK_ENV=production
SECRET_KEY=clave_super_secreta_diferente
```

### Usar WSGI server
```bash
pip install gunicorn
gunicorn app:app
```

### Configurar HTTPS
- Usar certificados SSL
- Configurar proxy reverso (nginx)
- Actualizar URLs en Supabase settings

## Backups

### Backup de base de datos
En Supabase, ve a **Settings** > **Database** > **Backups** para configurar backups automáticos.

### Backup manual
```sql
-- Exportar datos
SELECT * FROM users;
SELECT * FROM investments;
```

## Monitoreo

### Logs de aplicación
Agregar logging a `app.py`:
```python
import logging
logging.basicConfig(level=logging.INFO)
```

### Métricas de Supabase
Revisar el dashboard de Supabase para métricas de uso y performance.

## Seguridad

### Mejores prácticas
- Nunca commitear el archivo `.env`
- Usar HTTPS en producción
- Mantener las dependencias actualizadas
- Revisar regularmente los logs de acceso

### Actualizar dependencias
```bash
pip list --outdated
pip install --upgrade package_name
```