# MorseLang

Lenguaje de programación cuyo código fuente se escribe en código Morse.
TP integrador de Lenguajes Formales y Compiladores.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Uso — CLI

```bash
python main.py examples/hola.morse              # ejecuta
python main.py examples/factorial.morse --tts   # + narra con ElevenLabs
python main.py archivo.morse --tokens           # solo tokens
python main.py archivo.morse --ast              # solo AST
```

## Uso — MORSE.LAB (UI visual)

UI web propia con backend Flask y frontend HTML/CSS/JS hecho a mano (estética CRT phosphor + tipografía editorial italic):

```bash
flask --app web.server run --port 5173
# → abrir http://127.0.0.1:5173
```

Cuatro vistas: **Editor** (escribir / ejecutar / ver tokens y AST), **Audio** (subir .wav, decodificar, mandar al editor), **Inspector** (las 7 partes del TP en vivo), **Ayuda** (tablas Morse y de keywords).

Alternativa rápida con Streamlit (más simple, menos pulida):

```bash
streamlit run studio/app.py
```

## Tests

```bash
pytest -q
```

74 tests cubriendo lexer, parser, semántico, intérprete, TTS, decoder de audio, AST y CLI.

## Variables de entorno

Para `--tts`:

- `ELEVENLABS_API_KEY` — clave de API.
- `ELEVENLABS_VOICE_ID` — id de la voz (default: voz multilingüe estándar).

Ver `.env.example`.

## Estructura

```
morselang/        # paquete del compilador
  morse.py        # codec Morse <-> texto
  tokens.py       # modelo de tokens
  lexer.py        # tokenizador
  ast_nodes.py    # nodos del AST + to_dict
  parser.py       # parser recursivo descendente (LL(1))
  symbol_table.py # tabla de símbolos
  semantic.py     # análisis semántico
  interpreter.py  # intérprete tree-walking (con on_step opcional)
  tts.py          # cliente ElevenLabs
  audio.py        # decoder Morse desde audio (DSP)
studio/           # UI Streamlit
  app.py          # entry point
  components.py   # helpers compilador → estado
  pages/          # una página por archivo
examples/         # programas de ejemplo (.morse)
tests/            # pytest
docs/             # informe + bitácora de IA + tp_resources
.claude/skills/morselang-compiler/SKILL.md   # skill para Claude
main.py           # CLI
```

## Defensa del TP

Ver `docs/informe.md` y abrir el Studio para una vista interactiva de las 7 Partes del TP.
