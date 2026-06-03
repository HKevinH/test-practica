# Orquestador Notificador de Chats

PoC para interceptar mensajes, enviarlos a una API y decidir si requieren atención inmediata.

## Arquitectura

- `n8n` genera un payload JSON simulado con `user` y `message`.
- La API en Python expone `POST /webhook`.
- Si el mensaje contiene `urgente`, `error` o `ayuda`, devuelve `{"alert": true}`.
- Si no contiene esas palabras, devuelve `{"alert": false}`.

## Requisitos

- Docker y Docker Compose
- Node.js 18+ para Cypress

## Variables de entorno

El proyecto lee su configuración desde un archivo `.env` (no se sube a git). Antes de levantar nada, créalo a partir de la plantilla:

```bash
cp .env.example .env     # Linux/Mac
copy .env.example .env   # Windows
```

Variables disponibles:

| Variable | Descripción |
|----------|-------------|
| `N8N_ENCRYPTION_KEY` | Clave de cifrado de n8n. En local cualquier string sirve; en producción usa una aleatoria. |
| `API_WEBHOOK_URL` | URL a la que el workflow de n8n hace el POST. Local: `http://api:8000/webhook`. Para la demo con AWS, reemplaza por tu URL pública. |

## Levantar localmente

1. Arranca la API y n8n (toma los valores del `.env`):

```bash
docker compose up --build
```

2. Abre n8n en:

```text
http://localhost:5678
```

3. Importa el workflow desde `n8n-workflow.json`.
4. Ejecuta el workflow manualmente.

La API queda disponible en:

```text
http://localhost:8000
```

## Probar la API

Ejemplo de request:

```bash
curl -X POST http://localhost:8000/webhook ^
  -H "Content-Type: application/json" ^
  -d "{\"user\":\"Ana\",\"message\":\"Necesito ayuda urgente\"}"
```

Respuesta esperada:

```json
{"alert":true}
```

## Cypress

Instalar dependencias:

```bash
npm install
```

Ejecutar pruebas:

```bash
npm run cypress:run
```

El archivo de prueba está en:

- `cypress/e2e/webhook.cy.js`

## API en AWS

La guía recomendada de despliegue está en [`AWS_DEPLOYMENT.md`](AWS_DEPLOYMENT.md).

La API ya está contenedorizada, así que puedes subirla directamente a AWS App Runner, EC2, Elastic Beanstalk o Lambda + API Gateway.

## Evidencia de IA

Ver `IA_PROMPTS.md` para el registro de prompts usados durante la construcción de la prueba.
