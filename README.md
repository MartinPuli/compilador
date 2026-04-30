# MorseLang

> Un lenguaje de programación cuyo **código fuente se escribe en código Morse**.
> TP integrador de Lenguajes Formales y Compiladores — Python 3.12, todo a mano, **74 tests**.

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

## Defensa del TP

1. Mostrar el repo y `git log` (los commits cuentan la historia: lexer → tokens → parser → semántico → intérprete → TTS → audio decoder → UI).
2. `pytest -q` → mostrar los **74 tests verdes**.
3. Abrir MORSE.LAB → recorrer **Inspector** mostrando cada Parte del TP en vivo.
4. Cargar `factorial.morse` en el Editor → ejecutar → mostrar `120` y la tabla de símbolos.
5. Generar audio: `python main.py examples/factorial.morse --tts` → reproducir `output.mp3`.
6. **Audio → Morse**: subir un `.wav` con beeps → decodificar → mandar al editor → ejecutar.
7. Mostrar `docs/informe.md` (la teoría del TP) y `docs/uso_ia.md` (la bitácora obligatoria de uso de IA).
