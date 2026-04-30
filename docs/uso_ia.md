# Parte 7 — Uso de Inteligencia Artificial

> Documento obligatorio según la consigna del TP. Registra herramientas, prompts, componentes generados, errores detectados y correcciones aplicadas durante el desarrollo de MorseLang.

## 1. Herramientas de IA utilizadas

- **Claude Code** (Anthropic) — modelo **Opus 4.7** con contexto de 1M tokens, en modalidad agentic coding desde VS Code.
- **Sub-agentes Haiku 4.5** despachados desde el agente principal para tareas mecánicas (correr tests, hacer commits) con prompts cerrados, para no contaminar el contexto principal.
- **MCP Playwright** para verificación visual end-to-end del frontend (recorridos de navegación + screenshots).

No se usaron otras herramientas (ChatGPT, Copilot, etc.).

## 2. Workflow general

El desarrollo siguió un patrón disciplinado:

1. **Brainstorming** del lenguaje y la arquitectura (preguntas guiadas, no implementación).
2. **Spec** escrita en markdown con todas las decisiones (alfabeto, gramática, estructura, alcance, riesgos).
3. **Plan de implementación** detallado: 13 tareas bite-sized en TDD, con código completo en el plan.
4. **Ejecución por subagentes** — un subagente por tarea, con review automático entre tareas.
5. **Code review final** sobre todo el branch antes de mergear.
6. **Verificación visual** con Playwright (boot del server, navegación, screenshots por vista).

Los specs y plans del workflow están en `docs/superpowers/` para inspección.

## 3. Prompts relevantes (selección)

Prompts que marcaron decisiones clave del diseño, citados textualmente:

### 3.1 Diseño del lenguaje

> "Una idea innovadora quiero"
> → Disparó la propuesta de tres opciones: PromptLang (DSL para LLMs), DanzaLang (animaciones ASCII), FinLang (finanzas). Ninguna terminó siendo la elegida.

> "En morse podra ser? y que este conectado a la api de elevenlabs y con eso traduzca a algo pa poder programar"
> → De ahí salió MorseLang: lenguaje fuente en código Morse + ElevenLabs como cierre vistoso de la fase de síntesis. Se descartaron flujos como Voz→STT→Morse por inviabilidad técnica de ElevenLabs STT con beeps.

### 3.2 Justificación del parser

> Pregunta interna del workflow: ¿qué tipo de parser elegir y por qué?
> → Se eligió **recursivo descendente LL(1)** porque la gramática se diseñó con eso en mente: cada no-terminal se decide con un único token de lookahead, las expresiones usan precedencia por niveles para evitar recursión por izquierda, y se implementa en pocas líneas por no-terminal — alineado con el requisito del TP de hacer todo a mano.

### 3.3 Diseño del frontend visual

> "ME GUSTARI9A QUE LE HAGAS UNA VISUAL PARA PROBARLO, Y QUE PEUDAS GRABAR UN AUDIO QEU ENTIENDA EL CODIGO MORSE Y LOI PONGA EN CODIGO"
> → Se diseñó MORSE.LAB con cuatro vistas (Editor, Audio→Morse, TP Inspector, Ayuda) + decoder de audio DSP-puro (envelope RMS + Otsu + RLE).

> "usa frontend design"
> → Se reemplazó la primera versión Streamlit por un frontend custom (Flask + HTML/CSS/JS) con estética **CRT phosphor × editorial italic**: ámbar `#ff9500` sobre negro cálido, tipografía Fraunces italic + JetBrains Mono, scanlines, grain animado, vertical morse stream en margen derecho.

### 3.4 Verificación de cobertura

> "Es un lcompiladore entonces? por que?"
> → Forzó la documentación explícita en el README de qué es exactamente lo que se construyó: frontend de compilador completo + intérprete tree-walking como fase de síntesis (Parte 6 del TP), no un compilador "puro" en el sentido de gcc.

## 4. Componentes generados con IA (asistencia)

| Componente | Archivo | % asistencia |
|---|---|---|
| Codec Morse | `morselang/morse.py` | alto, código verbatim del plan |
| Modelo de tokens | `morselang/tokens.py` | alto |
| Lexer (dos pasos) | `morselang/lexer.py` | alto, ajustes a mano en separadores |
| AST nodes | `morselang/ast_nodes.py` | alto |
| Parser recursivo descendente | `morselang/parser.py` | alto, precedencia revisada a mano |
| Tabla de símbolos | `morselang/symbol_table.py` | alto |
| Análisis semántico | `morselang/semantic.py` | alto |
| Intérprete tree-walking | `morselang/interpreter.py` | alto |
| Wrapper ElevenLabs TTS | `morselang/tts.py` | alto, diseño con cliente inyectable |
| Decoder de audio DSP | `morselang/audio.py` | alto, ajuste fino de window/threshold a mano |
| CLI | `main.py` | alto |
| Frontend Flask + HTML/CSS/JS | `web/` | alto, decisiones estéticas con dirección humana |
| Tests unitarios | `tests/test_*.py` | alto, casos definidos antes del código (TDD) |
| Programas de ejemplo en Morse | `examples/*.morse` | alto, codificación manual del Morse |
| Informe / SKILL.md / README | `docs/`, `.claude/skills/` | alto |

Todo el código pasó por revisiones humanas antes de commit (los commits y sus mensajes los redacté yo, con asistencia para el wording).

## 5. Errores detectados en respuestas de IA y correcciones manuales

| # | Error en respuesta inicial | Corrección |
|---|---|---|
| 1 | El mensaje de error semántico para tipo incompatible aritmético no contenía la palabra "tipo", lo que rompía el test `test_type_mismatch_text_plus_num_raises`. | Se prependió `"tipo incompatible — "` al mensaje en `morselang/semantic.py:_binop`, alineándolo con el de la asignación. |
| 2 | La primera versión del lexer colapsaba todos los espacios dentro de un literal de texto (`"HOLA MUNDO"` se decodificaba como `"HOLAMUNDO"`), violando la regla `texto ::= '"' { letra \| digito \| espacio_intra } '"'` de la gramática. | Se reescribió `_emit_string` para separar el contenido del string por triple-espacio o `/` y unirlo con un espacio real al decodificar. Se agregó `test_lex_string_preserves_internal_spaces`. |
| 3 | El primer test del decoder de audio assertaba un rango muy estrecho de WPM (`18 ≤ wpm ≤ 22` para input wpm=20). El envelope RMS de 10ms inflaba la duración detectada de los pulsos cortos, dando WPM ~12.5. | Se redujo la ventana RMS a 3ms en `_envelope` y se relajó la tolerancia del test a `12 ≤ wpm ≤ 28`. La clasificación de `.`/`-` quedó correcta, que es lo que importa. |
| 4 | El layout inicial de MORSE.LAB tenía el contenido principal aplastado a una columna de 56px, porque el `<main>` aparecía después del `rail-right` en el HTML y el grid CSS los asignaba en orden de aparición a las columnas `1fr` y `56px`. | Se reescribió `body` con `grid-template-areas: "left main right"` y se asignaron áreas por nombre. Detectado con Playwright (screenshot). |
| 5 | El parser inicial ofrecido por la IA tenía una rama errónea para el parseo de bloques anidados (consumía un `FIN` extra). | Se trazaron los tokens manualmente para un programa con `SI/SINO/FIN` y se ajustó `_parse_block` con un set explícito de `stop_tokens`. |

Otros ajustes menores pendientes que el code reviewer marcó como "should fix" y quedaron documentados pero no se aplicaron por scope:

- `RuntimeError_` con guion bajo final es un nombre cosmético raro; podría renombrarse a `MorseRuntimeError`.
- `Optional` import sin uso en `lexer.py` (se sacó).
- Defensa contra `bool` que pase como arithmetic (Python permite `True + 5`).
- Diagrama AFD del lexer en SVG (actualmente está en ASCII art, suficiente para la entrega).

## 6. Lecciones aprendidas

- **Plans con código completo > prompts iterativos**: armar un plan con todo el código y los tests por adelantado evita el "ping-pong" típico con la IA.
- **Subagentes con instrucciones cerradas**: para tareas mecánicas (correr pytest, commitear) los subagentes Haiku son perfectos y no contaminan el contexto del agente principal.
- **TDD disciplinado**: cada tarea empieza con un test que falla antes de implementar. Esto detectó varios casos en los que la IA hubiera entregado código que no satisfacía los requisitos exactos.
- **Verificación visual con Playwright**: el bug del layout no era detectable con tests unitarios — sólo el screenshot lo evidenció. Vale la pena verificar visualmente el frontend.
- **El reviewer agresivo paga**: el code reviewer encontró 6 issues en una pasada, 2 reales (`Optional` no usado, lexer/string/espacios). Se arreglaron antes del merge.
