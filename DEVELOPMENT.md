# Desarrollo - Termómetro Político

## Pre-requisitos

```bash
pip install -r requirements.txt
# o
conda install --file requirements.txt
```

## Ejecutar en modo DEVELOPMENT (con hot-reload)

Desde la raíz del proyecto:

```bash
# Con conda
conda run -p /ruta/a/env python -m uvicorn backend.app:app --host 127.0.0.1 --port 5000 --reload

# O directamente si conda está activado
python -m uvicorn backend.app:app --host 127.0.0.1 --port 5000 --reload
```

✅ Servidor en: **http://127.0.0.1:5000**  
📚 Documentación API: **http://127.0.0.1:5000/docs**  
⚡ Hot reload: Los cambios en `backend/` se recargan automáticamente

## Ejecutar en modo PRODUCTION (local)

```bash
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --workers 2
```

## Docker - Construcción y ejecución

### Build
```bash
docker build -t sentiment-api:latest .
```

### Run
```bash
docker run -d \
  -p 8888:8888 \
  -e APP_MODE=PRODUCTION \
  --name sentiment-api \
  sentiment-api:latest
```

### Verificar
```bash
curl http://localhost:8888/health
```

## Notas importantes

- **El bloque `if __name__ == '__main__'` ha sido removido** porque:
  - En Docker, Uvicorn se ejecuta directamente vía: `CMD ["uvicorn", "backend.app:app", ...]`
  - En desarrollo local, usamos: `python -m uvicorn backend.app:app --reload`
  - No hay conflicto entre ambos enfoques

- **El puerto en Docker es 8888** (no 8000), pero internamente en docker-compose se mapea correctamente

- **Hot-reload solo funciona en desarrollo** porque Uvicorn necesita ver archivos cambiados en el filesystem
