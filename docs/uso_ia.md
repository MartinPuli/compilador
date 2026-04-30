# Uso de IA en el desarrollo del compilador

## Herramientas usadas

- Claude Code (Anthropic) — modelo Opus 4.7.

## Prompts relevantes

- Diseño inicial del lenguaje: pedido de "una idea innovadora" para el TP, derivó en MorseLang (código fuente en Morse + síntesis con ElevenLabs).
- Diseño de la gramática EBNF y elección de operadores como palabras Morse (MAS/MENOS/POR/DIV/IGUAL/DIST/MEN/MAY/ASIG) en lugar de símbolos.
- Estrategia del lexer en dos pasos (decodificación Morse + clasificación).
- Implementación del parser recursivo descendente (un método por no-terminal).
- Reglas del análisis semántico (declaración previa, tipos, división por cero literal).
- Implementación del intérprete tree-walking con captura de salida.
- Wrapper sobre la API de ElevenLabs con cliente inyectable para tests.

## Componentes generados con asistencia

- `morselang/morse.py` — codec Morse (decode_letter, decode_word).
- `morselang/tokens.py` — Token, TokenType, KEYWORDS.
- `morselang/lexer.py` — Lexer con manejo de strings y separadores.
- `morselang/ast_nodes.py` — dataclasses del AST.
- `morselang/parser.py` — parser recursivo descendente.
- `morselang/symbol_table.py` — tabla de símbolos.
- `morselang/semantic.py` — análisis semántico.
- `morselang/interpreter.py` — intérprete tree-walking.
- `morselang/tts.py` — wrapper de ElevenLabs.
- `main.py` — CLI.
- Tests unitarios y end-to-end.
- Programas de ejemplo en Morse.

## Errores detectados en respuestas de IA

- Mensaje de error semántico para tipo incompatible aritmético no contenía la palabra "tipo", lo que rompía un test que la asertaba. Se corrigió prependiendo "tipo incompatible — " al mensaje.
- Caso particular del lexer cuando un string contiene espacios múltiples: `decode_word` colapsa todo, así que "HOLA MUNDO" no se puede representar con un espacio real entre palabras dentro de un string. Se documentó la limitación y los ejemplos usan una sola palabra ("HOLAMUNDO").
- (Anotar otros errores a medida que aparezcan al revisar el TP).

## Correcciones realizadas manualmente

- Ajuste del mensaje de error en `morselang/semantic.py:_binop` para satisfacer el test de tipo incompatible.
- Ajuste del ejemplo `hola.morse` y su test asociado para usar "HOLAMUNDO" sin espacio interno.
- (Completar a medida que se revisa el código contra el informe).
