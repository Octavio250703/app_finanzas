# 🚀 Investment Manager v2.0

Una aplicación web avanzada desarrollada en Flask para gestionar y analizar inversiones en tiempo real, con autenticación segura usando Supabase Auth y funcionalidades empresariales completas.

## ✨ Nuevas Funcionalidades v2.0

### 🏢 Sistema de Organismos
- **Gestión completa de organismos** - Crea y administra entidades donde realizas inversiones
- **Panel detallado por organismo** - Métricas financieras, gráficos y análisis específicos
- **Información de contacto** - Direcciones, teléfonos, emails y sitios web
- **Habilitación/Deshabilitación** - Control granular de organismos activos

### ⭐ Sistema de Calificaciones
- **Calificaciones por estrellas** - Evalúa organismos en múltiples criterios
- **Criterios de evaluación**:
  - Nivel de Riesgo
  - Potencial de Rentabilidad  
  - Agilidad y Burocracia
  - Transparencia
- **Calificaciones promedio** - Visualización de ratings consolidados

### 💬 Sistema de Chat/Mensajes
- **Chat por inversión** - Notas y comentarios específicos para cada inversión
- **Chat por organismo** - Discusiones y observaciones sobre entidades
- **Timestamps automáticos** - Registro temporal de todos los mensajes
- **Interfaz en tiempo real** - Experiencia de chat moderna

### 📊 Análisis y Gráficos Avanzados
- **Gráficos interactivos** - Powered by Chart.js
- **Distribución por moneda** - Visualización USD vs ARS
- **Portafolio por organismo** - Análisis detallado de composición
- **Dashboard empresarial** - Métricas consolidadas y KPIs

### 🎨 Nueva Interfaz
- **Barra lateral de navegación** - Organización mejorada de funcionalidades
- **Design system actualizado** - Colores, tipografías y espaciados consistentes
- **Responsive design** - Optimizado para móviles y tablets
- **Micro-interacciones** - Experiencia de usuario premium

## 🔥 Características Principales

### 🔐 Autenticación y Seguridad
- **Supabase Auth** - Autenticación robusta con JWT
- **Row Level Security (RLS)** - Aislamiento completo de datos por usuario
- **Políticas de acceso granulares** - Control fino de permisos
- **Sesiones persistentes** - Manejo automático de tokens

### 📈 Gestión de Inversiones
- **CRUD completo** - Crear, leer, actualizar y eliminar inversiones
- **Integración con organismos** - Vinculación automática de inversiones a entidades
- **Cálculos automáticos** - Rendimientos estimados en tiempo real
- **Soft delete** - Inhabilitación reversible con indicadores visuales
- **Múltiples monedas** - Soporte para ARS, USD, EUR, BRL, UYU

### 📊 Analytics y Reportes
- **Dashboard consolidado** - Métricas principales en tiempo real
- **Estadísticas por organismo** - Análisis detallado de rendimiento por entidad
- **Gráficos de distribución** - Visualización de portafolio por diversos criterios
- **Filtros dinámicos** - Segmentación por estado, moneda y organismo

### 💼 Características Empresariales
- **Multi-organismo** - Gestión de múltiples entidades de inversión
- **Sistema de evaluación** - Calificación y comparación de organismos
- **Trazabilidad completa** - Historial detallado de cambios y comentarios
- **Exportación de datos** - (Preparado para futuras implementaciones)

## 🛠️ Tecnologías

### Backend
- **Flask 2.3+** - Framework web ligero y potente
- **Supabase Client** - Integración completa con Supabase
- **Python 3.8+** - Lenguaje principal
- **PostgreSQL** - Base de datos robusta via Supabase

### Frontend
- **Bootstrap 5.3** - Framework CSS moderno
- **Chart.js** - Gráficos interactivos y responsivos
- **Font Awesome 6.4** - Iconografía completa
- **Vanilla JavaScript** - Sin dependencias adicionales

### DevOps
- **Gunicorn** - Servidor WSGI para producción
- **Environment Variables** - Configuración segura
- **Git** - Control de versiones

## 📦 Instalación

### 1. Clonar el Repositorio
```bash
git clone <tu-repositorio>
cd investment-manager
```

### 2. Configurar Entorno Virtual
```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate
# En macOS/Linux:
source venv/bin/activate
```

### 3. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno
Crear archivo `.env` en la raíz del proyecto:
```env
# Supabase Configuration
SUPABASE_URL=tu_supabase_url
SUPABASE_KEY=tu_supabase_anon_key
SUPABASE_SERVICE_KEY=tu_supabase_service_key

# Flask Configuration
SECRET_KEY=tu_secret_key_aleatoria
FLASK_ENV=development
```

### 5. Configurar Base de Datos
1. Ve al panel de Supabase → SQL Editor
2. Ejecuta el script `final_database_update.sql`
3. Verifica que todas las tablas se crearon correctamente

### 6. Configurar Autenticación Supabase
1. Ve a **Authentication** → **Settings**
2. Configura las URLs permitidas
3. Habilita proveedores de autenticación necesarios
4. Crea usuarios desde **Authentication** → **Users**

### 7. Ejecutar la Aplicación
```bash
python app.py
```

Accede a `http://localhost:5000`

## 🎯 Guía de Uso

### 1. Primer Acceso
1. **Crear usuario en Supabase** - Usa el panel de Authentication
2. **Iniciar sesión** - Usa email y contraseña configurados
3. **Crear primer organismo** - Define entidades donde inviertes
4. **Crear primera inversión** - Vincula a un organismo existente

### 2. Gestión de Organismos
- **Crear organismos** - Sidebar → Organismos → Nuevo Organismo
- **Ver detalles** - Click en cualquier organismo para análisis completo
- **Calificar organismos** - Usa el sistema de estrellas en vista detallada
- **Chat organizacional** - Agrega comentarios y notas

### 3. Gestión de Inversiones
- **Dashboard principal** - Visualización consolidada de portafolio
- **Nueva inversión** - Selecciona organismo y completa detalles
- **Vista detallada** - Análisis individual con chat integrado
- **Edición y gestión** - Modificación completa de parámetros

### 4. Análisis y Reportes
- **Gráficos automáticos** - Generación dinámica en organismos
- **Filtros de dashboard** - Segmentación por estado y habilitación
- **Métricas en tiempo real** - Cálculos automáticos de rendimientos

## 🗂️ Estructura del Proyecto

```
investment-manager/
├── 📄 app.py                    # Aplicación principal Flask
├── 📄 models.py                 # Modelos de datos y lógica de negocio
├── 📄 config.py                 # Configuración de la aplicación
├── 📄 requirements.txt          # Dependencias Python
├── 📄 .env                      # Variables de entorno (crear)
├── 📄 final_database_update.sql # Script de actualización de BD
├── 📁 templates/               # Templates Jinja2
│   ├── 📄 base_sidebar.html    # Layout base con navegación
│   ├── 📄 dashboard.html       # Dashboard principal
│   ├── 📄 organisms.html       # Lista de organismos
│   ├── 📄 view_organism.html   # Vista detallada de organismo
│   ├── 📄 create_organism.html # Formulario crear organismo
│   ├── 📄 create_investment.html # Formulario crear inversión
│   └── 📄 login.html           # Página de login
├── 📁 static/                  # Archivos estáticos
│   ├── 📁 css/
│   │   └── 📄 style.css        # Estilos principales
│   └── 📁 js/
│       └── 📄 main.js          # JavaScript principal
```

## 🔧 Configuración Avanzada

### Variables de Entorno
```env
# Desarrollo
FLASK_ENV=development
FLASK_DEBUG=True

# Producción
FLASK_ENV=production
FLASK_DEBUG=False
```

### Configuración de Supabase
1. **RLS habilitado** - Row Level Security activo en todas las tablas
2. **Políticas configuradas** - Acceso seguro por usuario
3. **Índices optimizados** - Performance mejorada en consultas

### Personalización
- **Colores**: Modifica variables CSS en `style.css`
- **Organismos default**: Actualiza opciones en `create_investment.html`
- **Monedas**: Agrega opciones en formularios de inversión

## 📊 Modelos de Datos

### Organismos
```sql
organisms {
  id: BIGSERIAL PRIMARY KEY
  user_uuid: UUID (FK auth.users)
  name: VARCHAR(200) NOT NULL
  full_name: VARCHAR(500)
  description: TEXT
  website: VARCHAR(255)
  contact_email: VARCHAR(255)
  contact_phone: VARCHAR(50)
  address: TEXT
  country: VARCHAR(100)
  enabled: BOOLEAN
  created_at: TIMESTAMPTZ
  updated_at: TIMESTAMPTZ
}
```

### Calificaciones
```sql
organism_ratings {
  id: BIGSERIAL PRIMARY KEY
  organism_id: BIGINT (FK organisms)
  user_uuid: UUID (FK auth.users)
  risk_level: DECIMAL(2,1)
  profitability_potential: DECIMAL(2,1)
  agility_bureaucracy: DECIMAL(2,1)
  transparency: DECIMAL(2,1)
  created_at: TIMESTAMPTZ
  updated_at: TIMESTAMPTZ
}
```

### Mensajes
```sql
investment_messages {
  id: BIGSERIAL PRIMARY KEY
  investment_id: BIGINT (FK investments)
  user_uuid: UUID (FK auth.users)
  message: TEXT NOT NULL
  created_at: TIMESTAMPTZ
  updated_at: TIMESTAMPTZ
}

organism_messages {
  id: BIGSERIAL PRIMARY KEY
  organism_id: BIGINT (FK organisms)
  user_uuid: UUID (FK auth.users)
  message: TEXT NOT NULL
  created_at: TIMESTAMPTZ
  updated_at: TIMESTAMPTZ
}
```

## 🚀 Deployment

### Preparación
1. Configura variables de entorno para producción
2. Actualiza `FLASK_ENV=production`
3. Configura URLs permitidas en Supabase

### Opciones de Deployment
- **Heroku** - Platform as a Service
- **Railway** - Modern deployment platform
- **DigitalOcean App Platform** - Managed hosting
- **VPS tradicional** - Con nginx + gunicorn

### Comandos de Producción
```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar con Gunicorn
gunicorn --bind 0.0.0.0:8000 app:app
```

## 🔒 Seguridad

### Implementadas
- ✅ **Row Level Security (RLS)** en Supabase
- ✅ **Autenticación JWT** con Supabase Auth
- ✅ **Variables de entorno** para secretos
- ✅ **Validación de formularios** client y server side
- ✅ **Políticas de acceso granulares**

### Recomendaciones
- 🔐 Usar HTTPS en producción
- 🔑 Rotar keys periódicamente
- 📝 Auditar accesos en Supabase
- 🛡️ Implementar rate limiting

## 📈 Roadmap Futuro

### v2.1 - Análisis Avanzado
- [ ] Reportes PDF automáticos
- [ ] Comparaciones entre organismos
- [ ] Alertas de vencimientos
- [ ] Análisis de performance histórica

### v2.2 - Colaboración
- [ ] Compartir portafolios
- [ ] Comentarios colaborativos
- [ ] Equipos de inversión
- [ ] Notificaciones en tiempo real

### v2.3 - Integración
- [ ] APIs de cotizaciones en tiempo real
- [ ] Importación de datos bancarios
- [ ] Integración con brokers
- [ ] Exportación a Excel/CSV

## 🤝 Contribución

1. Fork el proyecto
2. Crea tu feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 📞 Soporte

- 📧 **Email**: tu-email@dominio.com
- 📱 **Issues**: Usa GitHub Issues para reportar bugs
- 💬 **Discusiones**: GitHub Discussions para preguntas

## 🙏 Agradecimientos

- **Supabase** - Por la plataforma BaaS excepcional
- **Flask** - Por el framework web elegante
- **Bootstrap** - Por los componentes UI robustos
- **Chart.js** - Por las visualizaciones interactivas
- **Font Awesome** - Por la iconografía completa

---

💡 **¿Necesitas ayuda?** Revisa la documentación de [Supabase](https://supabase.com/docs) y [Flask](https://flask.palletsprojects.com/) para referencias adicionales.

🚀 **¡Happy Investing!** Gestiona tu portafolio como un profesional.