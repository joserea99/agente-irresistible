# 🚀 Despliegue en Railway

Tu aplicación está lista para subir a la nube. Sigue estos pasos:

## 1. Crear Repositorio en GitHub
1. Ve a [GitHub](https://github.com/new) y crea un nuevo repositorio llamado `irresistible-agent`.
2. No añadas README ni .gitignore (ya los tenemos).

## 2. Subir tu Código
Abre tu terminal en la carpeta del proyecto y ejecuta estos comandos (copia el URL de tu nuevo repo):

```bash
# Ya hemos inicializado el git localmente por ti
git branch -M main
git remote add origin https://github.com/TU_USUARIO/irresistible-agent.git
git push -u origin main
```

## 3. Conectar a Railway
1. Ve a [Railway.app](https://railway.app/).
2. Haz clic en **"New Project"** -> **"Deploy from GitHub repo"**.
3. Selecciona `irresistible-agent`.
4. Railway detectará automáticamente el archivo `Procfile` y comenzará a construir.

## 4. Configurar Variables
Antes de que termine el despliegue (o si falla), ve a la pestaña **Variables** en Railway y añade:

- `GOOGLE_API_KEY`: Pega tu clave de Gemini (la misma que usas localmente).

---

## ℹ️ Notas Importantes
- **Memoria:** Hemos incluido la "memoria base" (`irresistible_brain_db`) en el repositorio, así que tu agente llegará a la nube con lo que ya aprendió.
- **Login:** La base de datos de usuarios también se subió. Podrás entrar con `tester3@example.com` / `pass`.
- **Persistencia:** Si reinicias el servidor en Railway, cualquier *nuevo* conocimiento se perderá a menos que añadas un Volumen. Para empezar, esto es suficiente.
