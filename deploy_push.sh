#!/bin/bash
# Script Helper: Push cambios a GitHub para Deployment Render
# Uso: ./deploy_push.sh

set -e  # Exit on error

echo "================================================"
echo "  ARMONÍA-WEB - Push a GitHub para Deployment"
echo "================================================"
echo ""

# Check if we're in the right directory
if [ ! -f "render.yaml" ]; then
    echo "❌ ERROR: No se encuentra render.yaml"
    echo "   Ejecuta este script desde la raíz del proyecto"
    exit 1
fi

echo "✅ Directorio correcto detectado"
echo ""

# Show git status
echo "📋 Estado actual del repositorio:"
echo "-----------------------------------"
git status --short
echo ""

# Ask for confirmation
read -p "¿Continuar con git add y commit? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "❌ Operación cancelada"
    exit 1
fi

# Add files
echo ""
echo "📦 Añadiendo archivos..."
git add render.yaml DEPLOY.md DEPLOY_STEP_BY_STEP.md app.py requirements.txt brain/task.md

# Show what will be committed
echo ""
echo "📝 Archivos que se commitearán:"
echo "-----------------------------------"
git status --short
echo ""

# Ask for commit message (or use default)
echo "💬 Mensaje de commit (Enter para usar default):"
read -p "   Default: 'feat: preparación deployment Render - lazy loading + config' " commit_msg
echo ""

if [ -z "$commit_msg" ]; then
    commit_msg="feat: preparación deployment Render - lazy loading + config

- Añadir render.yaml con config optimizada (1 worker, timeout 120s)
- Implementar lazy loading music21 para RAM 512 MB
- Crear DEPLOY.md y DEPLOY_STEP_BY_STEP.md con guía completa
- Actualizar requirements.txt documentación
- Actualizar brain/task.md con estado FASE 3B"
fi

# Create commit
echo "📌 Creando commit..."
git commit -m "$commit_msg"

# Detect branch name
branch=$(git rev-parse --abbrev-ref HEAD)
echo ""
echo "🌿 Branch detectada: $branch"
echo ""

# Ask before push
read -p "¿Push a origin/$branch? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "❌ Push cancelado (commit local creado)"
    exit 1
fi

# Push
echo ""
echo "🚀 Pushing a GitHub..."
git push origin "$branch"

echo ""
echo "================================================"
echo "  ✅ PUSH COMPLETADO"
echo "================================================"
echo ""
echo "Próximos pasos:"
echo "1. Ve a https://github.com/TU_USUARIO/Armonia-Web"
echo "2. Verifica que aparecen los nuevos archivos"
echo "3. Continúa con PASO 2 en DEPLOY_STEP_BY_STEP.md"
echo ""
