# Ya Leí ✓✓

[English](README.md) · **Español**

> Tus grupos de WhatsApp, ya leídos.

**Ya Leí** es un [Agent Skill](https://claude.com/skills) open source para **Claude Cowork** (y Claude Code) que convierte tus grupos de WhatsApp más ruidosos en un resumen diario — decisiones tomadas, preguntas que te hicieron, fechas y compromisos, y una línea resumiendo el ruido — entregado **a ti y solo a ti**, por Gmail o en un dashboard local.

Sin bots metidos en tus grupos. Sin API de WhatsApp. Sin que un solo mensaje salga de tu máquina. Lee lo que ya está en tu propio disco.

## El problema

Todos tenemos *ese* grupo. 300 mensajes al día, y enterrado ahí: la única decisión, la pregunta que te hicieron *a ti*, la fecha que cambiaron. Leerlo todo es un trabajo de medio tiempo; no leerlo es deuda social.

## Cómo funciona

```
WhatsApp Escritorio (macOS)              Cualquier teléfono (fallback)
ChatStorage.sqlite  ──┐                  chats exportados .txt ──┐
                      ▼                                          ▼
        scripts/wa_digest.py                    scripts/parse_export.py
                      └──────────► extracto crudo ◄──────────────┘
                                       ▼
                  Claude (tarea programada de Cowork, corre local)
                  escribe el digest CON CRITERIO: qué importa,
                  qué se decidió, qué quedó sin responder
                                       ▼
                   digests/AAAA-MM-DD.md ──► Gmail (solo a ti)
                                        └──► dashboard/index.html
```

- **Modo primario (macOS):** WhatsApp Escritorio guarda sus mensajes en un SQLite legible (`~/Library/Group Containers/group.net.whatsapp.WhatsApp.shared/ChatStorage.sqlite`). El skill saca una copia a una carpeta temporal y lee la copia en **modo solo-lectura, pasivo**. Nunca toca la app, nunca automatiza tu cuenta, nunca llama a ninguna API.
- **Fallback universal (todo lo demás):** exporta un chat desde tu teléfono (*Grupo → Exportar chat → Sin archivos*), suelta el `.txt` en `exports/`, y listo.
- **La "transformación con criterio":** Claude no reformatea mensajes — los lee y decide qué te dolería haberte perdido. Un pipeline con cron reporta `mensajes: 300`; un agente te dice *"movieron la cena al sábado y Andrés sigue esperando tu respuesta"*.

## Instalación

1. Clona este repo (o descárgalo) en un lugar permanente:
   ```bash
   git clone https://github.com/jaircelisv/ya-lei.git
   ```
2. Agrégalo como skill:
   - **Claude Cowork:** agrega la carpeta `ya-lei` a tus skills de Cowork, o apunta una tarea de Cowork a la carpeta y pídele a Claude que siga `SKILL.md`.
   - **Claude Code:** copia o enlaza la carpeta en `.claude/skills/` (o `~/.claude/skills/`).
3. Copia `config.example.json` → `config.json` y define tus grupos (o `top_active`), idioma y tu propio correo.
4. Crea la tarea programada en Cowork: *Programadas → Nueva tarea*, diaria, con el prompt: **"Ejecuta el digest diario del skill ya-lei."**

> **Importante:** como el skill lee archivos locales, la tarea programada corre **en tu máquina** — tu computador debe estar despierto a la hora programada. Ese es el trade-off honesto a cambio de que tus chats jamás viajen a un servidor.

## Principios de privacidad (no negociables)

1. **Solo tú.** El digest se entrega a tu propio correo/dashboard. El skill se niega a enviar contenido de chats a cualquier otro destino.
2. **Local primero.** La extracción ocurre en tu máquina. `digests/`, `exports/` y `config.json` están en el `.gitignore` — tus datos no pueden terminar en un commit por accidente.
3. **Pasivo.** Nada automatiza ni suplanta tu cuenta de WhatsApp. Leer un archivo de tu propio disco no viola términos de ninguna API — no hay llamada de API que violar.
4. **Sin fallos silenciosos.** Si la extracción, la entrega o cualquier paso falla, el skill lo dice fuerte y claro en vez de inventar un digest.

## Compatibilidad

| Plataforma | Modo | Estado |
|---|---|---|
| macOS + WhatsApp Escritorio (App Store) | base de datos local (cero fricción) | ✅ verificado |
| Windows / Linux | fallback de export `.txt` | ✅ funciona (ritual de 15 segundos) |
| Solo teléfono | fallback de export `.txt` | ✅ funciona |

El esquema de la base de datos de WhatsApp no está documentado y puede cambiar con actualizaciones. Si eso pasa, el skill falla en voz alta y el fallback de export sigue funcionando.

## 🏆 Vibecoders League — Platzi (Reto 6)

Este proyecto fue construido para el **Proyecto 6: "El reporte que se arma y se envía solo"** de la Vibecoders League de Platzi.

- **Fuente de datos real:** mis propios grupos de WhatsApp — más de 6.000 mensajes reales a la semana en esta misma máquina.
- **Transformación con criterio:** el digest lo escribe Claude con juicio propio (decisiones / preguntas sin responder / compromisos / ruido ignorable), no es un reenvío de datos crudos.
- **Envío automático y programado:** una tarea programada de Claude Cowork lo ejecuta a diario y lo entrega por Gmail + dashboard local.
- **Qué lo hace distinto:** no es un workflow — es un **skill instalable y open source**. Cualquiera puede clonar este repo y amanecer mañana con sus grupos ya leídos. Y trata la privacidad como el producto: el reporte solo llega a su dueño, jamás a nadie más.

Construido en vivo en una sesión de "party mode" de BMad — una mesa redonda adversarial de personas de IA que mató dos ideas (QEPD la ruta por API de WhatsApp: la Groups API de Meta no sirve para grupos personales) antes de que esta sobreviviera.

## Licencia

[MIT](LICENSE) — haz lo que quieras, solo no nos eches la culpa.
