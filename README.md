# 🏙️ Iglesia Irresistible OS - Sistema Operativo Ministerial

Una plataforma integral de Inteligencia Artificial diseñada para equipos ministeriales, experta en la estrategia de la **Iglesia Irresistible** de Andy Stanley.

## 🚀 Arquitectura

**Backend**: FastAPI (Python) - API REST con Gemini AI  
**Frontend**: Next.js (TypeScript) - Interfaz moderna y responsiva  
**Base de Datos**: SQLite (local) / PostgreSQL (producción)

---

## ✨ Funcionalidades Principales

### 1. 🏛️ El Gabinete (Consultoría Estratégica)
Obtén asesoría de 6 directores especializados:
- **Pastor Principal**: Visión, predicación, liderazgo
- **Programación de Servicio**: Experiencia dominical
- **Niños (NextGen)**: Estrategia Orange, seguridad
- **Estudiantes**: Cultura juvenil, grupos pequeños
- **Adultos (Grupos)**: Discipulado, cuidado pastoral
- **Servicios Ministeriales**: Operaciones, finanzas, sistemas

### 2. 🥋 El Dojo (Simulador de Liderazgo)
Entrena conversaciones difíciles en 3 escenarios:
- **El Padre Enojado**: Manejo de crisis con padres
- **El Voluntario Agotado**: Retención de líderes
- **El Invitado Escéptico**: Defensa de la estrategia

**Características**:
- Roleplay realista con IA
- Evaluación basada en principios de Iglesia Irresistible
- Soporte bilingüe (Español/English)

### 3. 📚 Base de Conocimiento (RAG)
- Sube documentos (PDF, Excel, CSV, TXT)
- Búsqueda inteligente con IA
- Contexto para respuestas personalizadas

### 4. 🧠 Smart Learning (Brandfolder)
- Integración con Brandfolder API
- Indexación automática de recursos
- Transcripción de medios (próximamente)

---

## 🛠️ Instalación Local

### Prerrequisitos
- Python 3.11+
- Node.js 18+
- Google Gemini API Key ([obtener aquí](https://aistudio.google.com/app/apikey))

### Backend (FastAPI)

```bash
# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
cd backend
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Edita .env y agrega tu GOOGLE_API_KEY

# Ejecutar servidor
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

El backend estará disponible en: `http://localhost:8000`

### Frontend (Next.js)

```bash
# Instalar dependencias
cd frontend
npm install

# Ejecutar en desarrollo
npm run dev
```

El frontend estará disponible en: `http://localhost:3000`

---

## 📁 Estructura del Proyecto

```
irresistible_agent/
├── backend/
│   ├── app/
│   │   ├── models/          # Modelos Pydantic
│   │   ├── routers/         # Endpoints API
│   │   │   ├── auth.py      # Autenticación
│   │   │   ├── chat.py      # El Gabinete
│   │   │   ├── dojo.py      # El Dojo
│   │   │   └── brandfolder.py
│   │   └── services/        # Lógica de negocio
│   │       ├── chat_service.py
│   │       ├── dojo_service.py
│   │       └── auth_service.py
│   ├── main.py              # Aplicación FastAPI
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── login/           # Página de login
│   │   ├── dashboard/       # Dashboard principal
│   │   ├── chat/            # El Gabinete
│   │   ├── dojo/            # El Dojo (próximamente)
│   │   └── knowledge/       # Base de conocimiento
│   ├── components/          # Componentes reutilizables
│   └── lib/                 # Utilidades y stores
├── DEPLOY.md                # Guía de despliegue
├── ENV_SETUP.md             # Variables de entorno
└── README.md                # Este archivo
```

---

## 🌐 API Endpoints

### Autenticación
- `POST /auth/login` - Iniciar sesión
- `POST /auth/register` - Registrar usuario

### Chat (El Gabinete)
- `GET /chat/directors` - Listar directores disponibles
- `POST /chat/message` - Enviar mensaje y recibir respuesta
- `POST /chat/export` - Exportar conversación a Word

### Dojo (Simulador)
- `GET /dojo/scenarios?language=es` - Listar escenarios
- `POST /dojo/start` - Iniciar escenario
- `POST /dojo/message` - Enviar mensaje en roleplay
- `POST /dojo/evaluate` - Evaluar desempeño

### Documentación Interactiva
Visita `http://localhost:8000/docs` para ver la documentación completa de la API (Swagger UI)

---

## 🚀 Despliegue en Railway

Consulta [DEPLOY.md](./DEPLOY.md) para instrucciones detalladas.

**Resumen rápido**:
1. Sube el código a GitHub
2. Conecta Railway con tu repositorio
3. Configura variables de entorno (`GOOGLE_API_KEY`, `SECRET_KEY`)
4. ¡Listo! Railway desplegará automáticamente

---

## 🔑 Credenciales de Prueba

Para pruebas locales:
- **Usuario**: `tester3@example.com`
- **Contraseña**: `pass`

> ⚠️ **Importante**: Cambia estas credenciales en producción

---

## 🧪 Testing

### Backend
```bash
cd backend
pytest
```

### Frontend
```bash
cd frontend
npm test
```

---

## 📚 Tecnologías Utilizadas

### Backend
- **FastAPI**: Framework web moderno y rápido
- **LangChain**: Integración con Gemini AI
- **ChromaDB**: Base de datos vectorial para RAG
- **SQLite/PostgreSQL**: Base de datos relacional
- **Python-JOSE**: Autenticación JWT

### Frontend
- **Next.js 16**: Framework React con SSR
- **TypeScript**: Tipado estático
- **Tailwind CSS**: Estilos utilitarios
- **shadcn/ui**: Componentes UI
- **Zustand**: Gestión de estado
- **Framer Motion**: Animaciones

---

## 🤝 Contribuir

Este es un proyecto privado para la Red de Iglesia Irresistible. Si tienes sugerencias o encuentras bugs, contacta al administrador.

---

## 📄 Licencia

© 2026 Iglesia Irresistible OS - Todos los derechos reservados

---

## 🆘 Soporte

- **Documentación**: [DEPLOY.md](./DEPLOY.md), [ENV_SETUP.md](./ENV_SETUP.md)
- **API Docs**: `http://localhost:8000/docs`
- **Issues**: Contacta al administrador del sistema

---

*Construyendo iglesias que las personas sin iglesia aman asistir* 🏛️✨
