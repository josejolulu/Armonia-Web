# Guía Paso a Paso - Deployment en Render

**Proyecto**: Armonía-Web  
**Tiempo estimado**: 1.5 horas  
**Requisitos**: Cuenta GitHub (gratuita)

---

## PASO 1: Push Cambios a GitHub (15 minutos)

### 1.1 - Verificar Estado del Repositorio

Abre una nueva terminal y navega a tu proyecto:

```bash
cd /Users/joseluissanchez/Documents/Proyectos/Armonia-Web\ antigravity
```

Verifica qué archivos han cambiado:

```bash
git status
```

**Deberías ver aproximadamente**:

```
Changes not staged for commit:
  modified:   app.py
  modified:   requirements.txt
  modified:   brain/task.md
  
Untracked files:
  render.yaml
  DEPLOY.md
```

---

### 1.2 - Añadir Archivos al Staging

Añade **todos** los archivos modificados:

```bash
git add .
```

> **⚠️ IMPORTANTE**: El `.` añade TODO. Si solo quieres archivos específicos:
>
> ```bash
> git add render.yaml DEPLOY.md app.py requirements.txt brain/task.md
> ```

Verifica que se añadieron correctamente:

```bash
git status
```

**Deberías ver**:

```
Changes to be committed:
  new file:   DEPLOY.md
  modified:   app.py
  modified:   brain/task.md
  new file:   render.yaml
  modified:   requirements.txt
```

---

### 1.3 - Crear Commit

Crea un commit descriptivo:

```bash
git commit -m "feat: preparación deployment Render - lazy loading + config"
```

**Mensaje detallado alternativo** (más profesional):

```bash
git commit -m "feat: Preparación FASE 3B deployment

- Añadir render.yaml con config optimizada (1 worker, timeout 120s)
- Implementar lazy loading music21 para RAM 512 MB
- Crear DEPLOY.md con guía completa
- Actualizar requirements.txt documentación
- Actualizar brain/task.md con estado FASE 3B"
```

---

### 1.4 - Push a GitHub

Sube los cambios al repositorio remoto:

```bash
git push origin main
```

> **📝 Nota**: Si tu rama se llama `master` en lugar de `main`:
>
> ```bash
> git push origin master
> ```

**Si te pide autenticación**:

- GitHub ya NO acepta contraseñas desde 2021
- Necesitas un **Personal Access Token** (PAT)

#### Crear Personal Access Token (si es necesario)

1. Ve a: <https://github.com/settings/tokens>
2. Click **"Generate new token"** → **"Generate new token (classic)"**
3. Nombre: `Render Deployment`
4. Expiration: `No expiration` (o `90 days` si prefieres)
5. Scopes: Marca **`repo`** (acceso completo a repositorios)
6. Click **"Generate token"**
7. **COPIA EL TOKEN** (solo se muestra una vez)

Cuando Git pida contraseña, pega el token (no se mostrará al escribir).

**Verificar que subió correctamente**:

```bash
git log -1
```

Deberías ver tu commit más reciente.

---

### 1.5 - Verificar en GitHub (Web)

1. Abre tu navegador
2. Ve a: `https://github.com/TU_USUARIO/Armonia-Web`
3. Verifica que aparecen los nuevos archivos:
   - `render.yaml`
   - `DEPLOY.md`
   - `app.py` (modificado)

✅ **LISTO** - Código en GitHub

---

## PASO 2: Crear Cuenta en Render (5 minutos)

### 2.1 - Registrarse

1. Ve a: <https://render.com>
2. Click **"Get Started"** o **"Sign Up"**
3. **RECOMENDADO**: Usa **"Sign up with GitHub"**
   - Te pedirá autorizar Render en GitHub
   - Click **"Authorize Render"**
4. Completa perfil básico (nombre, email si no viene de GitHub)

✅ **LISTO** - Cuenta creada

---

## PASO 3: Crear Web Service en Render (10 minutos)

### 3.1 - Dashboard Inicial

Tras login, verás el **Dashboard de Render**:

- Arriba derecha: **"New +"** (botón azul)

Click en **"New +" → "Web Service"**

---

### 3.2 - Conectar Repositorio GitHub

**Pantalla: "Create a new Web Service"**

Verás lista de tus repositorios de GitHub. Si no aparece `Armonia-Web`:

1. Scroll hasta abajo
2. Click **"+ Connect account"** o **"Configure GitHub App"**
3. Autoriza acceso al repositorio `Armonia-Web`

**Selecciona tu repositorio**:

- Busca `Armonia-Web antigravity` (o como se llame)
- Click **"Connect"** (botón azul a la derecha)

---

### 3.3 - Configuración del Servicio

**Render detectará automáticamente `render.yaml`** y mostrará:

```
✅ Configuration file detected: render.yaml
```

**IMPORTANTE - Dos opciones**:

#### OPCIÓN A: Usar render.yaml (RECOMENDADO)

Si Render detectó `render.yaml`:

1. **NO MODIFIQUES NADA**
2. Render usará automáticamente la configuración del archivo
3. Scroll hasta abajo
4. Click **"Create Web Service"** (botón azul grande)

#### OPCIÓN B: Configuración Manual (si no detecta render.yaml)

Si NO aparece el mensaje de configuración detectada, configura manualmente:

**Name**: `armonia-web` (puedes cambiarlo)

**Region**: `Frankfurt (EU Central)`

**Branch**: `main` (o `master`)

**Runtime**: `Python`

**Build Command**:

```bash
pip install --no-cache-dir -r requirements.txt
```

**Start Command**:

```bash
gunicorn --workers 1 --timeout 120 --bind 0.0.0.0:$PORT app:app
```

**Instance Type**: **Free** (debería estar seleccionado por defecto)

**Environment Variables** (click "Advanced" si no aparecen):

- `PYTHON_VERSION` = `3.10`
- `FLASK_ENV` = `production`
- `WEB_CONCURRENCY` = `1`

Después de configurar, click **"Create Web Service"**

---

### 3.4 - Build en Progreso

Verás pantalla de **"Building..."** con logs en tiempo real:

```
==> Cloning repository from https://github.com/...
==> Checking out branch main
==> Detected Python application
==> Installing dependencies from requirements.txt
    Collecting Flask==3.1.2
    Collecting music21==9.9.1
    ...
    Successfully installed Flask-3.1.2 music21-9.9.1 gunicorn-23.0.0
==> Build successful in 187s
==> Deploying...
==> Your service is live 🎉
```

**Tiempo típico**: 3-5 minutos

> **Si falla el build**, ver sección [Troubleshooting](#troubleshooting) más abajo.

---

### 3.5 - Servicio Desplegado

Cuando termine, verás:

```
✅ Live
```

Y tu URL pública:

```
https://armonia-web.onrender.com
```

(o similar, puede tener hash: `armonia-web-abc123.onrender.com`)

✅ **LISTO** - Servicio desplegado

---

## PASO 4: Verificación (20 minutos)

### 4.1 - Primera Visita (Cold Start)

1. Copia la URL que te dio Render
2. Pégala en tu navegador
3. **ESPERA 30-60 segundos** la primera vez
4. Ver ás mensaje: "Service Unavailable" o spinner

> **Esto es NORMAL** - Es el cold start. Espera.

Después de ~60s, deberías ver la aplicación cargada.

---

### 4.2 - Verificar Interfaz

**¿Qué deberías ver?**

- ✅ Título: "AULA DE ARMONÍA"
- ✅ Pentagrama musical (VexFlow)
- ✅ Botón "Revisar"
- ✅ Panel lateral "Errores Detectados"

**Si ves errores de consola**:

1. Presiona `F12` (abrir DevTools)
2. Pestaña **"Console"**
3. Busca errores rojos
4. Ver sección [Troubleshooting](#troubleshooting)

---

### 4.3 - Probar Análisis Armónico

**Test básico**:

1. La app debería cargar con una progresión por defecto (I - V - I - vi)
2. Click **"Revisar"**
3. **ESPERA 5-10 segundos** (primera vez carga music21 lazy)
4. Deberías ver detección de errores (si los hay)

**Si aparece error "504 Gateway Timeout"**:

- Normal en primer request (lazy loading)
- Recarga página
- Intenta de nuevo

**Si después de 3 intentos sigue fallando**:

- Ver logs de Render (siguiente sección)

---

### 4.4 - Revisar Logs de Render

En el dashboard de Render:

1. Click en tu servicio `armonia-web`
2. Pestaña **"Logs"** (arriba)
3. Deberías ver:

```
INFO:app:music21 cargado (lazy loading)
INFO:app:Módulos de análisis cargados (lazy loading)
INFO:app:Analizando en tonalidad: C major
INFO:app:Motor de reglas armónicas inicializado
```

**Si ves errores**:

```
ERROR: ModuleNotFoundError: No module named 'music21'
```

→ Ver [Troubleshooting - Build](#troubleshooting)

---

### 4.5 - Verificar Tests (Opcional)

Si quieres asegurar que todo funciona:

```bash
# En tu terminal local
cd /Users/joseluissanchez/Documents/Proyectos/Armonia-Web\ antigravity

# Correr tests
python3 -m pytest tests/ -v
```

Deberían pasar 10/10 tests.

---

## PASO 5: Optimizaciones Opcionales (30 minutos)

### 5.1 - Keep-Alive (Evitar Cold Starts)

**Problema**: Render duerme la app tras 15 min de inactividad

**Solución**: Configurar un servicio que haga ping cada 14 minutos

#### Usando UptimeRobot (GRATIS)

1. Ve a: <https://uptimerobot.com>
2. **Sign Up** (gratis, no requiere tarjeta)
3. Click **"Add New Monitor"**
4. Configuración:
   - **Monitor Type**: HTTP(s)
   - **Friendly Name**: `Armonia-Web Keep-Alive`
   - **URL**: `https://armonia-web.onrender.com/`
   - **Monitoring Interval**: `Every 5 minutes` (opción más cercana a 14)
5. Click **"Create Monitor"**

**Resultado**: Tu app NUNCA se dormirá ✅

> **⚠️ Nota Ética**: Render permite esto en free tier. No es abuso siempre que:
>
> - Sea tu propia app educational
> - No generes tráfico artificial masivo
> - Uses para pruebas/demos

---

### 5.2 - Custom Domain (Opcional)

Si tienes un dominio propio (ej: `armonia.tudominio.com`):

1. En Render Dashboard → tu servicio
2. Pestaña **"Settings"**
3. Sección **"Custom Domain"**
4. Click **"Add Custom Domain"**
5. Introduce: `armonia.tudominio.com`
6. Render te dará un registro CNAME
7. Añádelo en tu proveedor DNS

**No es necesario para funcionalidad**, solo para URL personalizada.

---

## PASO 6: Actualizar Documentación (10 minutos)

### 6.1 - Actualizar README.md

Edita `README.md` en tu proyecto:

```markdown
# Armonía-Web

Aplicación web para análisis armónico musical.

## 🚀 Demo en Vivo

**URL**: https://armonia-web.onrender.com

> ⚠️ Nota: Primera carga puede tardar 30-60s (cold start)

## Tecnologías

- Backend: Flask + music21
- Frontend: VexFlow 4.2.2
- Deployment: Render (tier gratuito)

## Estado del Proyecto

✅ FASE 3A Completada - 14 reglas armónicas implementadas  
✅ FASE 3B Completada - Deployment en producción
```

Sube cambios:

```bash
git add README.md
git commit -m "docs: añadir URL demo en vivo"
git push origin main
```

---

## Troubleshooting

### Error: Build Failed - "ModuleNotFoundError"

**Causa**: `requirements.txt` tiene dependencia que no se puede instalar

**Solución**:

1. Revisa logs de build en Render
2. Identifica qué paquete falló
3. Verifica versión en `requirements.txt`
4. Si es `music21`, puede tardar mucho en instalar (es normal)

**Timeout en build**:

Si el build excede 15 minutos, Render lo cancela. `music21` puede causar esto.

**Solución temporal**:

- Edita `requirements.txt` temporalmente
- Comenta `music21==9.9.1` con `#`
- Push
- Espera a que build pase
- Descomenta `music21`
- Push de nuevo

---

### Error: "Application failed to respond"

**Causa**: App no seBindea al puerto correcto

**Solución**:

Verifica que `app.py` al final tenga:

```python
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)
```

O mejor aún, que uses `gunicorn` (ya configurado en `render.yaml`).

---

### Error: "504 Gateway Timeout"

**Causa**: Request tarda más de 120 segundos

**Soluciones**:

1. **Normal en primer request** (lazy loading music21)
   - Recarga página y vuelve a intentar

2. **Si persiste**:
   - Verifica logs en Render
   - Busca `ERROR` o `CRITICAL`

3. **Increase timeout** (ya está en 120s en render.yaml):

   ```yaml
   startCommand: gunicorn --workers 1 --timeout 180 --bind 0.0.0.0:$PORT app:app
   ```

---

### Error: "502 Bad Gateway"

**Causa**: Servicio crasheó

**Solución**:

1. Ve a Render Dashboard
2. Click tu servicio
3. Pestaña **"Logs"**
4. Busca último error antes de crash
5. Típicamente:
   - `MemoryError` → RAM insuficiente (ver abajo)
   - `ImportError` → Dependencia faltante

**Si es RAM insuficiente**:

Render free tier = 512 MB. Con `music21` estás al límite.

**Opciones**:

a) **Upgrade a Starter Plan** ($7/mes → 1GB RAM)
b) **Optimizar más**:

- Desactivar features no críticas temporalmente
- Reducir imports

---

### Render Se Queda en "Deploying..." Por Horas

**Causa**: Build Loop o configuración incorrecta

**Solución**:

1. Click **"Manual Deploy" → "Clear build cache & deploy"**
2. Si falla de nuevo, **Suspend Service**
3. Revisa `render.yaml` - verifica sintaxis
4. Resume service

---

## Monitoreo y Mantenimiento

### Ver Logs en Tiempo Real

```bash
# En terminal (requiere Render CLI)
# Instalar CLI:
npm install -g render-cli

# Login
render login

# Ver logs
render logs armonia-web --tail
```

O directamente en web: Dashboard → Service → Logs tab

---

### Actualizar Aplicación

**Cada vez que hagas cambios**:

```bash
git add .
git commit -m "fix: corregir bug X"
git push origin main
```

**Render detectará el push automáticamente** y rebuild (~3-5 min).

---

### Desactivar Servicio (Si Quieres Parar)

1. Render Dashboard → tu servicio
2. **Settings** → Scroll abajo
3. **"Suspend Service"** (no se borra, solo pausa)

**Reactivarlo**:

- Settings → **"Resume Service"**

---

## Resumen de Comandos

```bash
# 1. Push cambios a GitHub
cd /Users/joseluissanchez/Documents/Proyectos/Armonia-Web\ antigravity
git status
git add .
git commit -m "feat: deployment render"
git push origin main

# 2. Verificar deployment
# (hacer en navegador en Render.com)

# 3. Verificar logs
# Dashboard Render → Logs tab

# 4. Actualizar README
git add README.md
git commit -m "docs: añadir URL demo"
git push origin main
```

---

## Checklist Final

- [ ] Código en GitHub (render.yaml, DEPLOY.md, app.py)
- [ ] Cuenta Render creada
- [ ] Web Service creado en Render
- [ ] Build completado exitosamente
- [ ] URL pública funciona
- [ ] Interfaz carga correctamente
- [ ] Análisis armónico funciona (botón "Revisar")
- [ ] Logs no muestran errores críticos
- [ ] (Opcional) Keep-alive configurado (UptimeRobot)
- [ ] (Opcional) README.md actualizado con URL demo

---

## Próximos Pasos

✅ **FASE 3B COMPLETADA** - Deployment en producción  

**Siguiente**: FASE 4 - Grados y Cifrados  
O  
**Migración VexFlow 5.0** (planificada)

---

## Recursos Adicionales

- [Render Flask Docs](https://render.com/docs/deploy-flask)
- [Gunicorn Config](https://docs.gunicorn.org/en/stable/settings.html)
- [music21 Docs](https://web.mit.edu/music21/doc/)
- [UptimeRobot](https://uptimerobot.com)

---

**¿Problemas no resueltos?**

Revisa logs de Render y comparte el error específico.
