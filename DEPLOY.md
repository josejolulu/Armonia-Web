# Deployment en Render - Guía Rápida

## 📋 Archivos de Configuración

- ✅ `render.yaml` - Configuración de servicio
- ✅ `requirements.txt` - Dependencias Python (gunicorn incluido)
- ✅ `app.py` - Optimizado para 512 MB RAM (lazy loading)

---

## 🚀 Pasos para Deploy

### 1. Crear cuenta en Render

- Ir a [render.com](https://render.com)
- Registrarse con GitHub (recomendado)

### 2. Crear Web Service

1. Dashboard → **New +** → **Web Service**
2. Conectar repositorio GitHub
3. Seleccionar rama `main`
4. Render detectará automáticamente `render.yaml`

### 3. Configuración Automática

El archivo `render.yaml` configura:

- Runtime: Python 3.10
- Workers: 1 (optimizado para RAM)
- Timeout: 120 segundos
- Región: Frankfurt (Europa)

### 4. Deploy

- Click **Create Web Service**
- Build tarda ~3-5 minutos
- URL pública: `https://armonia-web.onrender.com`

---

## ⚙️ Configuración Avanzada (Opcional)

### Keep-Alive para Evitar Cold Starts

Usar [UptimeRobot](https://uptimerobot.com) (gratis):

1. Crear monitor HTTP(S)
2. URL: `https://armonia-web.onrender.com`
3. Intervalo: Cada 14 minutos
4. **Resultado**: App nunca se duerme

### Monitoreo

```bash
# Ver logs en tiempo real
render logs --tail

# Ver uso de RAM
render dashboard
```

---

## 🐛 Troubleshooting

### Build falla

```bash
# Verificar localmente
pip install -r requirements.txt
python app.py
```

### RAM overflow

1. Verificar que `WEB_CONCURRENCY=1` en envVars
2. Monitorear con `render logs --tail`
3. Si persiste: Upgrade a Render Starter ($7/mes → 1GB RAM)

### Cold start muy lento

- Implementar keep-alive (UptimeRobot)
- O upgrade a paid tier (sin sleep)

---

## 📊 Recursos (Free Tier)

- RAM: 512 MB
- CPU: Compartida
- Bandwidth: Ilimitado
- Build time: 750 horas/mes
- **Limitación**: App se duerme tras 15 min inactividad

---

## ✅ Verificación Post-Deploy

1. Abrir `https://armonia-web.onrender.com`
2. Probar análisis armónico (primero tardará ~30-60s - cold start)
3. Verificar 10/10 tests pasan
4. Actualizar README.md con URL pública

---

## 📚 Documentación

- [Render Python Apps](https://render.com/docs/deploy-flask)
- [render.yaml Reference](https://render.com/docs/yaml-spec)
- [Free Tier Limits](https://render.com/docs/free)
