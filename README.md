# MorseLang

Lenguaje de programación cuyo código fuente se escribe en código Morse.
TP integrador de Lenguajes Formales y Compiladores.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Uso

```bash
python main.py examples/hola.morse              # ejecuta
python main.py examples/factorial.morse --tts   # ejecuta + narra con ElevenLabs
python main.py archivo.morse --tokens           # solo tokens
python main.py archivo.morse --ast              # solo AST
```

## Tests

```bash
pytest -q
```

## Variables de entorno

Para `--tts`:

- `ELEVENLABS_API_KEY` — clave de API
- `ELEVENLABS_VOICE_ID` — id de la voz (default: voz multilingüe estándar)

Ver `.env.example`.

## Estructura

```
morselang/        # paquete del compilador
  morse.py        # codec Morse <-> texto
  tokens.py       # modelo de tokens
  lexer.py        # tokenizador
  ast_nodes.py    # nodos del AST
  parser.py       # parser recursivo descendente (LL(1))
  symbol_table.py # tabla de símbolos
  semantic.py     # análisis semántico
  interpreter.py  # intérprete tree-walking
  tts.py          # cliente ElevenLabs
examples/         # programas de ejemplo (.morse)
tests/            # pytest
docs/             # informe + bitácora de IA + spec/plan
main.py           # CLI
```
