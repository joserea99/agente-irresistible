# Variables de Entorno para Railway

## Variables Requeridas

### 1. GOOGLE_API_KEY
**Descripción**: API Key de Google Gemini para el servicio de IA  
**Cómo obtenerla**: 
1. Ve a [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Crea una nueva API Key
3. Copia la clave

**Ejemplo**: `AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`

---

### 2. SECRET_KEY
**Descripción**: Clave secreta para JWT (autenticación)  
**Cómo generarla**: Usa cualquier string aleatorio seguro

**Ejemplo**: `tu-clave-secreta-super-segura-aqui-12345`

**Generar una segura** (ejecuta en terminal):
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

### 3. DATABASE_URL (Opcional para Railway)
**Descripción**: URL de la base de datos PostgreSQL  
**Railway**: Se configura automáticamente si agregas un servicio PostgreSQL

**Formato**: `postgresql://user:password@host:port/database`

**Nota**: Si no se configura, la app usará SQLite (no recomendado para producción)

---

## Variables Opcionales

### 4. FRONTEND_URL
**Descripción**: URL del frontend para CORS  
**Valor en Railway**: La URL que Railway asigne a tu servicio

**Ejemplo**: `https://irresistible-agent-production.up.railway.app`

---

### 5. BRANDFOLDER_API_KEY
**Descripción**: API Key de Brandfolder (solo si usas Smart Learning)  
**Cómo obtenerla**: Solicítala a tu administrador de Brandfolder

---

## Configuración en Railway

### Paso 1: Ir a Variables
1. Abre tu proyecto en Railway
2. Selecciona tu servicio
3. Ve a la pestaña **Variables**

### Paso 2: Agregar Variables
Haz clic en **+ New Variable** y agrega cada una:

```
GOOGLE_API_KEY=tu_clave_aqui
SECRET_KEY=tu_clave_secreta_aqui
```

### Paso 3: (Opcional) Agregar PostgreSQL
1. Haz clic en **+ New** → **Database** → **Add PostgreSQL**
2. Railway creará automáticamente la variable `DATABASE_URL`

### Paso 4: Redesplegar
Después de agregar las variables, haz clic en **Deploy** para aplicar los cambios.

---

## Verificación

Para verificar que las variables están configuradas correctamente:

1. Ve a la URL de tu app: `https://tu-app.up.railway.app/`
2. Deberías ver: `{"status": "online", "message": "Irresistible Agent API v2.0 is running 🚀"}`
3. Prueba el endpoint de salud: `https://tu-app.up.railway.app/health`

---

## Troubleshooting

### Error: "No Google Gemini API Key configured"
- Verifica que `GOOGLE_API_KEY` esté configurada
- Asegúrate de que no tenga espacios al inicio o final

### Error: "Database connection failed"
- Si usas PostgreSQL, verifica que `DATABASE_URL` esté configurada
- Si no necesitas PostgreSQL aún, la app funcionará con SQLite

### Error de CORS
- Agrega `FRONTEND_URL` con la URL de tu frontend
- O actualiza `backend/main.py` para incluir tu dominio en `origins`
