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

## Uso — Studio (UI visual)

```bash
streamlit run studio/app.py
```

Cuatro páginas: Editor, Audio→Morse (decodifica .wav o grabación de mic), TP Inspector (Partes 1-7 en vivo), Ayuda.

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
