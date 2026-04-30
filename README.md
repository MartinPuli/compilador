# MorseLang

> Un lenguaje de programación cuyo **código fuente se escribe en código Morse**.
> TP integrador de Lenguajes Formales y Compiladores — Python 3.12, todo a mano, **74 tests**.

🌐 **Demo live:** [compilador-swart.vercel.app](https://compilador-swart.vercel.app/)
📦 **Repo:** [github.com/MartinPuli/compilador](https://github.com/MartinPuli/compilador)
📄 **Informe PDF:** [`docs/informe.pdf`](docs/informe.pdf)

```
.... --- .-.. .-   --   ..- -. -.. ---
   →   "HOLA MUNDO"
```

---

## ¿Es un compilador?

Pregunta legítima — y la respuesta honesta tiene matices.

**Definiciones estrictas:**

- **Compilador**: traduce el código fuente a un *artefacto de salida* (bytecode, código máquina, otro lenguaje fuente) que después se ejecuta por separado. `gcc`, `javac`, `tsc` lo son.
- **Intérprete**: ejecuta el código fuente directamente, sin producir un archivo intermedio. Python (CPython al ejecutar `.py` desde la línea de comandos) y Bash lo son.

**Lo que tenemos en este repo:**

| Fase | ¿Está? | Implementación |
|---|---|---|
| Análisis léxico | ✓ | `morselang/lexer.py` (AFD a mano + clasificación) |
| Análisis sintáctico | ✓ | `morselang/parser.py` (recursivo descendente LL(1)) |
| Construcción de AST | ✓ | `morselang/ast_nodes.py` |
| Tabla de símbolos | ✓ | `morselang/symbol_table.py` |
| Análisis semántico | ✓ | `morselang/semantic.py` |
| **Síntesis: intérprete** | ✓ | `morselang/interpreter.py` (tree-walking) |
| Síntesis: generador de código a otro lenguaje | ✗ | (no se hizo) |

Es decir, el **frontend** es un compilador completo. El **backend** elegido es un intérprete tree-walking en lugar de un generador de código.

**¿Por qué eso cuenta como "compilador" para el TP?**

La consigna del TP, en la **Parte 6 — Fase de síntesis**, dice literalmente:

> *"Seleccione una opción: Intérprete del lenguaje / Generador de código (pseudo-código, C, ensamblador simple, etc.) / Traductor a otro lenguaje."*

Es decir, el profesor reconoce explícitamente que la fase de síntesis puede ser un intérprete y eso satisface la consigna. Por eso el repo se llama "compilador" (es como lo enmarca la materia y el TP).

**Cómo presentarlo en la defensa:**

> *"MorseLang es un compilador de MorseLang con fase de síntesis interpretada. El frontend (lexer + parser + AST + análisis semántico + tabla de símbolos) es lo que clásicamente lleva un compilador como gcc; la diferencia es que en lugar de generar bytecode o código máquina, el AST se ejecuta directamente con un intérprete tree-walking. La consigna del TP acepta esta variante en la Parte 6."*

Si se quisiera convertir esto en un compilador "puro", agregar un traductor `MorseLang → Python` o `MorseLang → pseudo-código` son ~80–150 líneas más; no se hizo porque el intérprete cierra mejor el círculo (con la integración de ElevenLabs como cierre vistoso).

---

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows
pip install -r requirements.txt
```

Python 3.11+ (probado en 3.12).

---

## Uso — CLI

```bash
python main.py examples/hola.morse              # ejecuta
python main.py examples/factorial.morse --tts   # + narra con ElevenLabs
python main.py archivo.morse --tokens           # solo tokens
python main.py archivo.morse --ast              # solo AST
```

Códigos de salida: `0` éxito, `1` error de compilador (léxico/sintáctico/semántico/runtime), `2` archivo no encontrado.

---

## Uso — MORSE.LAB (UI visual recomendada)

Frontend custom: Flask + HTML/CSS/JS hecho a mano, estética CRT phosphor (ámbar sobre negro) + tipografía editorial italic (Fraunces serif + JetBrains Mono).

```bash
flask --app web.server run --port 5173
# → http://127.0.0.1:5173
```

Cuatro vistas:

- **Editor** — escribir / pegar código, ejecutar, ver tokens y AST, tabla de símbolos final.
- **Audio** — subir un `.wav` con beeps Morse, decodificarlo (DSP a mano: envelope RMS + Otsu + RLE), mandarlo al editor.
- **Inspector** — pestañas con cada Parte del TP (1 a 7) en vivo: alfabeto, EBNF, AFD, AST en vivo, snapshot por sentencia de la tabla, galería de errores semánticos.
- **Ayuda** — tablas Morse de letras, dígitos, keywords y operadores.

Alternativa rápida (más simple, menos pulida): `streamlit run studio/app.py`.

---

## Tests

```bash
pytest -q
```

74 tests cubriendo lexer, parser, semántico, intérprete, TTS, decoder de audio, AST y CLI.

---

## Variables de entorno

Para `--tts`:

- `ELEVENLABS_API_KEY` — clave de API.
- `ELEVENLABS_VOICE_ID` — id de la voz (default: voz multilingüe estándar).

Ver `.env.example`.

---

## Sintaxis del lenguaje (resumen)

| Texto | Morse | Rol |
|---|---|---|
| `VAR` | `...- .- .-.` | declaración |
| `MOSTRAR` | `-- --- ... - .-. .- .-.` | print |
| `SI` / `SINO` / `FIN` | `... ..` / `... .. -. ---` / `..-. .. -.` | condicional |
| `MIENTRAS` | `-- .. . -. - .-. .- ...` | bucle |
| `ASIG` | `.- ... .. --.` | `=` |
| `MAS` `MENOS` `POR` `DIV` | `-- .- ...` `-- . -. --- ...` `.--. --- .-.` `-.. .. ...-` | aritmética |
| `IGUAL` `DIST` `MEN` `MAY` | comparaciones | `==` `!=` `<` `>` |
| `VERDADERO` / `FALSO` | literales booleanos | |

**Separadores:**

- 1 espacio entre letras de una palabra.
- 3 espacios o `/` entre tokens.
- Salto de línea entre sentencias.
- Comillas `"..."` para literales de texto, contenido también en Morse.

Tabla completa y ejemplos: ver `Ayuda` en el Studio o `docs/informe.md`.

---

## Estructura

```
morselang/        # núcleo del compilador
  morse.py        # codec Morse ↔ texto
  tokens.py       # modelo de tokens
  lexer.py        # tokenizador
  ast_nodes.py    # nodos del AST + to_dict
  parser.py       # parser recursivo descendente (LL(1))
  symbol_table.py # tabla de símbolos
  semantic.py     # análisis semántico
  interpreter.py  # intérprete tree-walking (con on_step opcional)
  tts.py          # cliente ElevenLabs
  audio.py        # decoder Morse desde audio (DSP)

web/              # MORSE.LAB — UI custom (Flask + HTML/CSS/JS)
  server.py       # backend con la API JSON
  templates/      # index.html
  static/         # style.css + app.js

studio/           # alternativa Streamlit (legacy, más simple)

examples/         # programas de ejemplo (.morse)
tests/            # pytest (74 tests)
docs/             # informe.md + uso_ia.md + tp_resources.py + specs/plans
.claude/skills/morselang-compiler/SKILL.md   # skill de Claude
main.py           # CLI
requirements.txt
```

---

## Deploy a Vercel

El repo ya está configurado para deploy serverless en Vercel (archivos `api/index.py`, `api/requirements.txt`, `vercel.json`). Tres formas:

### Opción 1 — Web (más simple)

1. Crear cuenta en https://vercel.com con tu GitHub.
2. **New Project** → **Import** → seleccionar el repo `MartinPuli/compilador`.
3. Vercel detecta automáticamente Python (no toca nada).
4. (Opcional) en **Environment Variables** agregar `ELEVENLABS_API_KEY` si querés TTS — el server web no lo usa, pero se queda guardada por las dudas.
5. **Deploy**. Te da una URL del estilo `compilador-xxxx.vercel.app`.

### Opción 2 — CLI

```bash
npm i -g vercel
vercel login
vercel              # primer deploy: te pregunta nombre, scope, etc.
vercel --prod       # promueve a producción
```

### Opción 3 — Conectar y auto-deploy

Después de la Opción 1, cada `git push` a `main` dispara un deploy automático en Vercel.

**Limitaciones del deploy serverless:**

- **Cold start** ~5-10s la primera request (después queda caliente unos minutos).
- **Tamaño:** numpy + scipy son grandes, el deploy entra apretado en el límite de 50MB de Vercel free. Si falla, hay que reescribir `morselang/audio.py` para usar solo numpy (eliminar `scipy.signal.convolve` y `scipy.io.wavfile`).
- **TTS no funciona en serverless** — la integración con ElevenLabs solo está en el CLI (`python main.py archivo.morse --tts`), no en el web server. Mover una request de TTS a Vercel funcionaría pero el audio resultante puede pasar el límite de respuesta serverless.
- **El Studio de Streamlit no se deploya** acá — Streamlit necesita un server persistente, no es WSGI. Si querés deploy de la UI Streamlit, usar Render.com o Streamlit Cloud.

**Alternativas si Vercel da problemas:**

- **Render.com** (gratis, mejor para Flask): conectar repo → "Web Service" → Build Command: `pip install -r requirements.txt` → Start: `gunicorn web.server:app`.
- **Railway.app**: similar a Render, también gratis con créditos.
- **Fly.io**: gratis con Dockerfile.

---

## Uso de IA en el desarrollo (Parte 7 del TP)

La consigna del TP permite explícitamente usar IA siempre que esté documentada. El detalle completo (prompts, errores detectados, correcciones manuales) está en [`docs/uso_ia.md`](docs/uso_ia.md). Resumen:

- **Herramienta:** Claude Code (Anthropic) — modelo Opus 4.7 con contexto de 1M tokens, en VS Code. Sub-agentes Haiku 4.5 para tareas mecánicas (correr tests, commitear). MCP Playwright para verificación visual del frontend.
- **Workflow:** brainstorming → spec en markdown → plan TDD detallado con todo el código → ejecución task-por-task con review automático → code review final. Los specs y plans del workflow están en `docs/superpowers/`.
- **Componentes generados con asistencia:** todo el código del compilador (`morselang/`), el frontend web (`web/`), los tests (74 en total), los ejemplos en Morse y la documentación. Todo pasó por revisión humana antes del commit.
- **Errores corregidos a mano:** mensaje de error semántico para tipo incompatible (no contenía la palabra "tipo"), lexer colapsando espacios dentro de strings, parámetros del DSP del decoder de audio mal calibrados, layout grid del frontend mal asignado. Cada uno con su explicación y fix en `docs/uso_ia.md`.
- **Patrón clave:** el plan tenía el **código completo** de cada tarea antes de empezar a programar. Eso evitó el "ping-pong" típico con la IA y produjo commits limpios y reversibles.

---

## Cumplimiento de la consigna del TP

| Parte del TP | Estado | Dónde |
|---|---|---|
| 1 — Definición del lenguaje | ✓ | `docs/informe.md` §1 + Studio TP Inspector tab 01 |
| Alfabeto | ✓ | informe + `tp_resources.py:ALFABETO` |
| Tokens | ✓ | `morselang/tokens.py` + tabla en informe |
| Gramática EBNF | ✓ | `tp_resources.py:EBNF` + informe |
| Ejemplo de derivación | ✓ | `tp_resources.py:DERIVACION` + informe |
| 2 — Análisis léxico | ✓ | `morselang/lexer.py`, `morselang/morse.py` |
| Lista de tokens con regex | ✓ | tabla en `docs/informe.md` §2 |
| Autómata (AFD) | ✓ | ASCII art en informe + Studio Inspector tab 02 |
| Implementación | ✓ | `morselang/lexer.py` (a mano, sin Flex/PLY) |
| Ejemplo de tokens | ✓ | `python main.py X.morse --tokens` o trace en vivo en Studio |
| 3 — Análisis sintáctico | ✓ | `morselang/parser.py`, `morselang/ast_nodes.py` |
| Tipo y justificación | ✓ | recursivo descendente LL(1) — explicado en informe §3 |
| Implementación | ✓ | `morselang/parser.py` (a mano) |
| Ejemplo con árbol | ✓ | `--ast` o vista AST en vivo en Studio |
| 4 — Tabla de símbolos | ✓ | `morselang/symbol_table.py` |
| Información almacenada | ✓ | tipo, valor, línea de declaración |
| Inserción y consulta | ✓ | `declarar` / `asignar` / `consultar` / `existe` / `snapshot` |
| Ejemplo de uso | ✓ | snapshot paso a paso en Studio Inspector tab 04 |
| 5 — Análisis semántico | ✓ | `morselang/semantic.py` |
| Reglas | ✓ | 7 reglas documentadas en informe §5 |
| Tipos de errores | ✓ | tabla con mensajes exactos |
| Ejemplos | ✓ | `examples/error_*.morse` + galería en Studio Inspector tab 05 |
| 6 — Fase de síntesis (a elección) | ✓ | **Intérprete del lenguaje** (tree-walking) |
| Implementación | ✓ | `morselang/interpreter.py` + `morselang/tts.py` (extra: ElevenLabs) |
| 7 — Uso de IA | ✓ | `docs/uso_ia.md` |
| Herramientas | ✓ | Claude Code Opus 4.7 |
| Prompts relevantes | ✓ | sección 3 de `uso_ia.md` con citas textuales |
| Componentes generados | ✓ | tabla completa |
| Errores detectados | ✓ | 5 casos documentados |
| Correcciones manuales | ✓ | cada uno con fix detallado |
| **Entregables** | | |
| Informe en PDF | ✓ | `docs/informe.pdf` (regenerable con `py -3.12 tools/build_informe_pdf.py`) |
| Código fuente | ✓ | repo completo |
| Ejemplos de ejecución | ✓ | `examples/*.morse` + screenshots/Studio + demo en https://compilador-swart.vercel.app/ |

---

## Defensa del TP

1. Mostrar el repo y `git log` (los commits cuentan la historia: lexer → tokens → parser → semántico → intérprete → TTS → audio decoder → UI).
2. `pytest -q` → mostrar los **74 tests verdes**.
3. Abrir MORSE.LAB → recorrer **Inspector** mostrando cada Parte del TP en vivo.
4. Cargar `factorial.morse` en el Editor → ejecutar → mostrar `120` y la tabla de símbolos.
5. Generar audio: `python main.py examples/factorial.morse --tts` → reproducir `output.mp3`.
6. **Audio → Morse**: subir un `.wav` con beeps → decodificar → mandar al editor → ejecutar.
7. Mostrar `docs/informe.md` (la teoría del TP) y `docs/uso_ia.md` (la bitácora obligatoria de uso de IA).
