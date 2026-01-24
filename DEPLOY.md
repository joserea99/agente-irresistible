# 🚀 Guía de Despliegue en Railway

Esta aplicación ahora usa **FastAPI (Backend)** + **Next.js (Frontend)**. Esta guía te ayudará a desplegar el backend en Railway.

---

## 📋 Prerrequisitos

1. Cuenta en [Railway.app](https://railway.app/)
2. Cuenta en [GitHub](https://github.com/)
3. Google Gemini API Key ([obtener aquí](https://aistudio.google.com/app/apikey))

---

## 🔧 Paso 1: Preparar el Repositorio

### 1.1 Crear Repositorio en GitHub

1. Ve a [GitHub](https://github.com/new)
2. Crea un nuevo repositorio llamado `irresistible-agent`
3. **NO** añadas README ni .gitignore (ya los tenemos)

### 1.2 Subir el Código

Abre tu terminal en la carpeta del proyecto:

```bash
# Inicializar git (si no está inicializado)
git init

# Agregar todos los archivos
git add .

# Hacer commit
git commit -m "Initial commit - FastAPI + Next.js migration"

# Conectar con tu repositorio
git branch -M main
git remote add origin https://github.com/TU_USUARIO/irresistible-agent.git

# Subir a GitHub
git push -u origin main
```

---

---

## 🚂 Paso 2: Desplegar en Railway (Backend y Frontend)

Como tienes un proyecto con Backend (FastAPI) y Frontend (Next.js) en el mismo repositorio (Monorepo), deberás crear **dos servicios** en Railway conectados al mismo repositorio.

### 2.1 Desplegar el Backend

1.  En Railway, **New Project** → **Deploy from GitHub repo** → selecciona `irresistible-agent`.
2.  Una vez creado, ve a **Settings** del servicio.
3.  Busca la sección **Service** > **Root Directory**.
4.  Escribe: `/backend`
5.  Railway detectará la configuración y usará el comando de inicio correcto (`uvicorn...`).
6.  **Variables de Entorno**: Configura las variables (Ver Paso 3) en este servicio.
7.  **Domain**: Genera un dominio (ej: `backend-irresistible.up.railway.app`).

### 2.2 Desplegar el Frontend

1.  En el mismo proyecto de Railway, haz clic en **+ New** → **GitHub Repo** → selecciona `irresistible-agent` (otra vez).
2.  Esto creará un segundo servicio.
3.  Ve a **Settings** de este nuevo servicio.
4.  **Root Directory**: Escribe `/frontend`
5.  **Build Command**: `npm run build`
6.  **Start Command**: `npm start`
7.  **Variables de Entorno**:
    *   `NEXT_PUBLIC_API_URL`: Pon la URL de tu backend (ej: `https://backend-irresistible.up.railway.app`).
    *   `SECRET_KEY`: **CRÍTICO**. Debe ser la MISMA clave que pusiste en el Backend. Si no coinciden, no podrás entrar.
    *   **IMPORTANTE**: Esta variable debe ser accesible por el navegador, así que asegúrate de que el Backend tenga HTTPS (Railway lo da por defecto).
8.  **Domain**: Genera un dominio para el frontend (ej: `irresistible-app.up.railway.app`).

---

## ⚙️ Paso 3: Configurar Variables del Backend


### 3.1 Variables Requeridas

Ve a la pestaña **Variables** en Railway y agrega:

#### GOOGLE_API_KEY
```
GOOGLE_API_KEY=tu_clave_de_gemini_aqui
```
[¿Cómo obtenerla?](https://aistudio.google.com/app/apikey)

#### SECRET_KEY
```
SECRET_KEY=tu_clave_secreta_super_segura
```

**Generar una clave segura:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3.2 Variables Opcionales

#### Para PostgreSQL (Recomendado para producción)
1. En Railway, haz clic en **"+ New"** → **"Database"** → **"Add PostgreSQL"**
2. Railway creará automáticamente `DATABASE_URL`

### 3.3 Configurar Persistencia (CRÍTICO)

Para evitar que se borre tu base de datos y tu base de conocimiento cada vez que actualizas:

1.  Ve a tu servicio **Backend** en Railway.
2.  Ve a la pestaña **Volumes**.
3.  Haz clic en **New Volume**.
4.  Mount Path: `/app/brain_data`
5.  Haz clic en **Add**.

> **¿Qué hace esto?** Crea un "disco duro" permanente. Ahora tu base de datos (`irresistible_app.db`) y tu cerebro (`irresistible_brain_db`) se guardarán aquí y **sobrevivirán** a los despliegues.

---

## 🔍 Paso 4: Verificar el Despliegue

### 4.1 Obtener la URL

1. En Railway, ve a **Settings** → **Domains**
2. Haz clic en **"Generate Domain"**
3. Copia la URL (ejemplo: `https://irresistible-agent-production.up.railway.app`)

### 4.2 Probar la API

Abre tu navegador y ve a:

```
https://tu-app.up.railway.app/
```

Deberías ver:
```json
{
  "status": "online",
  "message": "Irresistible Agent API v2.0 is running 🚀"
}
```

### 4.3 Probar Endpoints

**Health Check:**
```
GET https://tu-app.up.railway.app/health
```

**Listar Directores:**
```
GET https://tu-app.up.railway.app/chat/directors
```

**Listar Escenarios de Dojo:**
```
GET https://tu-app.up.railway.app/dojo/scenarios?language=es
```

---

## 🧪 Paso 5: Probar con el Frontend Local

Mientras el frontend no esté desplegado, puedes probarlo localmente:

### 5.1 Configurar Frontend Local

Edita `frontend/lib/store.ts`:

```typescript
export const api = axios.create({
    baseURL: 'https://tu-app.up.railway.app',  // ← Cambia esto
    headers: {
        'Content-Type': 'application/json',
    },
});
```

### 5.2 Ejecutar Frontend

```bash
cd frontend
npm install
npm run dev
```

Abre `http://localhost:3000` y prueba:
- Login
- Chat con directores
- El Dojo (cuando esté implementado)

---

## 📚 Endpoints Disponibles

### Autenticación
- `POST /auth/login` - Iniciar sesión
- `POST /auth/register` - Registrar usuario

### Chat (El Gabinete)
- `GET /chat/directors` - Listar directores
- `POST /chat/message` - Enviar mensaje
- `POST /chat/export` - Exportar conversación

### Dojo
- `GET /dojo/scenarios` - Listar escenarios
- `POST /dojo/start` - Iniciar escenario
- `POST /dojo/message` - Enviar mensaje en roleplay
- `POST /dojo/evaluate` - Evaluar desempeño

### Brandfolder
- `POST /brandfolder/search` - Buscar en Brandfolder
- (Otros endpoints existentes)

---

## 🐛 Troubleshooting

### El despliegue falla
- Verifica que todas las dependencias estén en `backend/requirements.txt`
- Revisa los logs en Railway: **Deployments** → Click en el deployment → **View Logs**

### Error: "No Google Gemini API Key configured"
- Asegúrate de haber agregado `GOOGLE_API_KEY` en Variables
- Verifica que no tenga espacios al inicio o final

### Error de CORS desde el frontend
- Agrega tu dominio del frontend a `backend/main.py` en la lista `origins`

### La base de datos se resetea
- Agrega PostgreSQL como se indica en el Paso 3.2
- SQLite no es persistente en Railway

---

## 🎯 Próximos Pasos

1. ✅ Backend desplegado y funcionando
2. ⏳ Desplegar frontend (Next.js) en Vercel o Railway
3. ⏳ Conectar frontend con backend
4. ⏳ Configurar dominio personalizado

---

## 📞 Soporte

Si tienes problemas:
1. Revisa los logs en Railway
2. Verifica que todas las variables de entorno estén configuradas
3. Consulta [ENV_SETUP.md](./ENV_SETUP.md) para detalles de variables

---

*Iglesia Irresistible OS © 2026 - Powered by FastAPI + Next.js*
