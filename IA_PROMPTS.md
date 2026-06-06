# Evidencia de uso de IA

Este documento registra cómo utilicé herramientas asistidas por IA (Claude en VS Code)
durante el desarrollo de la prueba técnica **"Orquestador Notificador de Chats"**.

No se trata solo de generar código: el valor estuvo en **diagnosticar bloqueos**, **tomar
decisiones de arquitectura** y **acelerar tareas de configuración** (Docker, n8n, AWS) en
las que no era experto desde el inicio.

---

## Metodología de trabajo con IA

1. **Contexto primero:** abrí los archivos relevantes en el editor para que la IA viera el
   código real, no descripciones aproximadas.
2. **Iteración corta:** pedí cambios pequeños y verificables en vez de "hazme todo".
3. **Pedir el porqué:** en cada decisión técnica exigí alternativas y trade-offs (ej. qué
   servicio de AWS, EC2 vs Lambda) antes de ejecutar.
4. **Verificación:** todo lo generado lo probé (curl, `docker ps`, prueba pública) antes de
   darlo por bueno.

---

## Fase 1 — Backend (API REST en Python)

### Prompt
> "Crea una API REST sencilla en Python con un endpoint `POST /webhook` que reciba
> `{ user, message }` y responda `{ alert: true/false }` si el texto contiene 'urgente',
> 'error' o 'ayuda', ignorando mayúsculas/minúsculas."

**Rol de la IA:** propuso FastAPI por su validación automática de payloads y la documentación
interactiva en `/docs`.
**Decisión tomada:** elegí FastAPI sobre Flask por la validación de tipos integrada y porque
genera OpenAPI sin esfuerzo, útil para la demo.
**Resultado:** endpoint con detección de keywords case-insensitive y un `/health` extra.

---

## Fase 2 — Contenerización (Docker + Compose)

### Prompt
> "Genera un Dockerfile funcional para una API Python con Uvicorn y un `docker-compose.yml`
> que levante la API junto con una instancia local de n8n para probar el flujo completo."

**Rol de la IA:** generó un Dockerfile con `python:3.11-slim`, variables
`PYTHONDONTWRITEBYTECODE`/`PYTHONUNBUFFERED` y un compose con los servicios `api` y `n8n`.
**Decisión tomada:** imagen *slim* para reducir tamaño; volumen persistente `n8n_data` para no
perder el workflow entre reinicios.

---

## Fase 3 — Workflow de n8n

### Prompt
> "Genera un workflow exportable de n8n con un trigger manual, un nodo Set que arme el payload
> `{ user, message }` y un nodo HTTP Request que haga POST a la API."

**Rol de la IA:** produjo el `n8n-workflow.json` con los tres nodos y sus conexiones.

---

## Fase 4 — 🔧 Bloqueo resuelto con IA: error `422 Unprocessable Entity`

Este fue el problema más interesante y el que mejor muestra el uso de IA para **depurar**.

### Síntoma
Al ejecutar el workflow, la API respondía en los logs:
```
chat-alert-api | "POST /webhook HTTP/1.1" 422 Unprocessable Entity
```

### Prompt
> "Mi API FastAPI devuelve 422 cuando n8n le hace POST a `/webhook`. ¿Por qué pasa y cómo lo
> diagnostico?"

**Diagnóstico de la IA:**
- El `422` lo lanza FastAPI **antes** de entrar a la función: el body no cumplió la validación
  del parámetro `payload: dict[str, Any] = Body(...)`.
- Revisando el `n8n-workflow.json`, el nodo HTTP Request usaba parámetros inválidos para la
  `typeVersion: 4` (`contentType` y `bodyParametersJson`), por lo que n8n no enviaba un cuerpo
  JSON válido ni el header `Content-Type: application/json`.

### Solución aplicada
Corregí el nodo a los parámetros correctos de la v4:
```diff
-  "contentType": "json",
-  "bodyParametersJson": "={{ JSON.stringify({ user: $json.user, message: $json.message }) }}"
+  "specifyBody": "json",
+  "jsonBody": "={{ JSON.stringify({ user: $json.user, message: $json.message }) }}"
```

**Aprendizaje:** la IA me ahorró buscar en la documentación de n8n al identificar que el
problema no estaba en la API sino en cómo el cliente serializaba el body.

---

## Fase 5 — Configuración por variables de entorno (refactor)

### Prompt
> "La URL de la API está hardcodeada en el compose y en el workflow. Quiero que salga de un
> `.env` para poder apuntar a local o a AWS sin tocar el código."

**Rol de la IA:** propuso:
- Variable `API_WEBHOOK_URL` en un archivo `.env` (con `.env.example` versionado y `.env`
  ignorado en git por contener la `N8N_ENCRYPTION_KEY`).
- El nodo n8n leyendo `={{ $env.API_WEBHOOK_URL || 'http://api:8000/webhook' }}`.
- Activar `N8N_BLOCK_ENV_ACCESS_IN_NODE=false`, porque n8n **bloquea** `$env` en expresiones
  por defecto (detalle que yo desconocía).

**Decisión tomada:** un único punto de cambio (el `.env`) para alternar entre local y la URL
pública de AWS sin modificar el workflow.

---

## Fase 6 — Pruebas automatizadas (Cypress)

### Prompt
> "Escribe un test en Cypress que haga POST directo a la API local (sin pasar por n8n) y
> verifique el caso `alert: true` y el caso `alert: false`."

**Rol de la IA:** generó dos casos con `cy.request` validando `status 200` y el body exacto.
**Decisión tomada:** `cy.request` en vez de `cy.visit` porque se prueba una API, no una UI.

---

## Fase 7 — Despliegue en AWS

### Prompt
> "Quiero desplegar solo la API en AWS gratis. ¿Qué servicio me conviene? Compara opciones de
> capa gratuita y su riesgo de costo."

**Rol de la IA:** comparó App Runner (sin free tier, cobra siempre), Lambda + API Gateway
(casi $0 pero requiere adaptar con Mangum) y EC2 `t3.micro` (gratis 12 meses, corre el Docker
tal cual).
**Decisión tomada:** **EC2 free-tier**, por ser lo más directo reutilizando el Dockerfile
existente y sin cambios de código.
**Apoyo adicional:** la IA generó la guía paso a paso (security group con puerto 8000,
instalación de Docker, `docker run`) y me ayudó a detectar que **faltaba la regla de entrada
del puerto 8000** en el security group cuando la API no respondía desde internet.

---

## Resumen del aporte de la IA

| Área | Aporte clave |
|------|--------------|
| Backend | Elección de FastAPI y lógica de keywords |
| Docker | Dockerfile slim + compose multi-servicio |
| Depuración | Diagnóstico del `422` (config del nodo n8n, no la API) |
| Arquitectura | Configuración por `.env` para alternar local/AWS |
| AWS | Comparativa de servicios y guía de EC2 + fix del security group |

El mayor valor no fue escribir código, sino **acelerar el diagnóstico de problemas** y
**fundamentar decisiones técnicas** en tecnologías diversas (n8n, Docker, AWS) en poco tiempo.
