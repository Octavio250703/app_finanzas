# Configuración de Supabase Auth - Guía Completa

## 1. Configuración Inicial

### Acceder al Panel de Supabase
1. Ve a [https://supabase.com](https://supabase.com)
2. Inicia sesión con tu cuenta
3. Selecciona tu proyecto
4. Navega a **Authentication**

## 2. Configuración de Authentication Settings

### Configuración General
1. Ve a **Authentication** > **Settings**
2. Configura las siguientes opciones:

#### User Signups
```
Enable email confirmations: Enabled
Enable phone confirmations: Disabled
```

#### Password Requirements
```
Minimum password length: 8
Require uppercase: Opcional
Require lowercase: Opcional  
Require numbers: Opcional
Require special characters: Opcional
```

#### Session Management
```
JWT expiry limit: 3600 (1 hora)
Refresh token rotation: Enabled
```

### Site URL
Configura la URL de tu aplicación:
```
Site URL: http://localhost:5000
```

### Redirect URLs
Agrega URLs de redirection permitidas:
```
Redirect URLs:
- http://localhost:5000
- http://localhost:5000/dashboard
```

## 3. Crear Usuarios

### Método 1: Desde el Panel de Supabase

1. Ve a **Authentication** > **Users**
2. Haz clic en **Add user**
3. Completa el formulario:
   ```
   Email: admin@ejemplo.com
   Password: MiPassword123!
   Email Confirm: true
   Phone Confirm: false
   ```
4. Haz clic en **Create user**

### Método 2: Via SQL (Opcional)
También puedes insertar usuarios directamente en la base de datos:

```sql
-- Nota: Esto es solo para referencia, usar el panel es más seguro
INSERT INTO auth.users (
  instance_id,
  id,
  aud,
  role,
  email,
  encrypted_password,
  email_confirmed_at,
  created_at,
  updated_at
) VALUES (
  '00000000-0000-0000-0000-000000000000',
  gen_random_uuid(),
  'authenticated',
  'authenticated',
  'admin@ejemplo.com',
  crypt('password123', gen_salt('bf')),
  now(),
  now(),
  now()
);
```

## 4. Configuración de Emails (Opcional)

### Plantillas de Email
1. Ve a **Authentication** > **Email Templates**
2. Personaliza las plantillas:
   - **Confirm signup**: Email de confirmación
   - **Magic Link**: Link mágico para login
   - **Reset Password**: Recuperación de contraseña

### Ejemplo de plantilla personalizada:
```html
<h2>Confirma tu cuenta</h2>
<p>Haz clic en el siguiente enlace para confirmar tu cuenta:</p>
<p><a href="{{ .ConfirmationURL }}">Confirmar cuenta</a></p>
<p>Si no creaste esta cuenta, puedes ignorar este email.</p>
```

## 5. Configuración SMTP (Para emails en producción)

### Configurar proveedor SMTP
1. Ve a **Authentication** > **Settings** > **SMTP Settings**
2. Configura tu proveedor:

#### Gmail/Google Workspace
```
SMTP Host: smtp.gmail.com
SMTP Port: 587
SMTP User: tu-email@gmail.com
SMTP Pass: tu-contraseña-de-aplicación
SMTP Admin Email: tu-email@gmail.com
```

#### SendGrid
```
SMTP Host: smtp.sendgrid.net
SMTP Port: 587
SMTP User: apikey
SMTP Pass: tu-api-key-de-sendgrid
SMTP Admin Email: noreply@tudominio.com
```

## 6. Verificar Configuración

### Probar Authentication
1. Ejecuta tu aplicación Flask
2. Ve a `http://localhost:5000`
3. Intenta iniciar sesión con las credenciales creadas
4. Verifica que puedas acceder al dashboard

### Debugear Problemas
1. Ve a **Authentication** > **Logs** en Supabase
2. Revisa los logs de autenticación
3. Busca errores o intentos fallidos

## 7. Usuarios de Ejemplo

### Crear varios usuarios para pruebas:

#### Usuario Administrador
```
Email: admin@ejemplo.com
Password: Admin123!
Rol: Administrador
```

#### Usuario Regular
```
Email: usuario@ejemplo.com  
Password: Usuario123!
Rol: Usuario regular
```

#### Usuario de Prueba
```
Email: test@ejemplo.com
Password: Test123!
Rol: Testing
```

## 8. Seguridad

### Mejores Prácticas
1. **Contraseñas seguras**: Exige al menos 8 caracteres
2. **Verificación de email**: Habilita confirmación por email
3. **Tokens de sesión**: Configura expiración apropiada
4. **Rate limiting**: Supabase lo maneja automáticamente
5. **HTTPS**: Usa siempre HTTPS en producción

### Políticas RLS
Las políticas de Row Level Security ya están configuradas en el script SQL:
```sql
-- Solo permiten acceso a datos propios del usuario
CREATE POLICY "Users can view own investments" ON investments
    FOR SELECT USING (auth.uid() = user_uuid);
```

## 9. Monitoreo

### Métricas de Authentication
1. Ve a **Authentication** > **Usage**
2. Revisa métricas:
   - Usuarios activos
   - Logins exitosos/fallidos
   - Registros nuevos
   - Sesiones activas

### Logs de Audit
1. Ve a **Authentication** > **Logs**
2. Filtra por:
   - Login attempts
   - Password resets
   - Email confirmations
   - Errors

## 10. Troubleshooting

### Problemas Comunes

#### "Invalid login credentials"
- Verificar que el usuario exista en Auth > Users
- Verificar que el email esté confirmado
- Verificar que el usuario no esté suspendido

#### "Email not confirmed"
- Ve a Auth > Users
- Haz clic en el usuario
- Marca "Email Confirmed" manualmente

#### "Session expired"
- Configurar JWT expiry más largo en Settings
- Implementar refresh token en la aplicación

#### "SMTP errors"
- Verificar configuración SMTP
- Probar con un proveedor diferente
- Revisar logs de email en Supabase

### Logs Útiles
```bash
# En tu aplicación Flask, agregar logging:
import logging
logging.basicConfig(level=logging.DEBUG)

# Esto te ayudará a ver errores de autenticación
```

## 11. Producción

### Checklist para Production
- [ ] Configurar dominio real en Site URL
- [ ] Configurar SMTP production
- [ ] Habilitar verificación de email
- [ ] Configurar políticas de contraseña estrictas
- [ ] Configurar backup de usuarios
- [ ] Monitorear métricas de auth
- [ ] Configurar alertas por intentos sospechosos

¡Con esta configuración tendrás un sistema de autenticación robusto y seguro para tu aplicación de gestión de inversiones!