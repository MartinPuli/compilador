# TP Integrador — Compilador MorseLang

## 1. Definición del lenguaje

- Descripción informal: lenguaje imperativo simple cuyo código fuente está escrito en código Morse.
- Alfabeto: `{ '.', '-', ' ', '/', '\n', '"' }`.
- Tokens: ver Parte 2.
- Gramática (EBNF): ver `docs/superpowers/specs/2026-04-29-morselang-design.md` sección 2.4.
- Ejemplo de derivación: ver spec sección 2.5.

## 2. Análisis léxico

- Lista de tokens y regex: ver spec sección 3.2.
- Autómata (AFD): diagrama TBD (pendiente para el informe final en PDF).
- Implementación: `morselang/lexer.py` (estrategia en dos pasos: decodificación Morse + clasificación).
- Ejemplo de ejecución: `python main.py examples/hola.morse --tokens`.

## 3. Análisis sintáctico

- Tipo: recursivo descendente (LL(1)).
- Justificación: gramática diseñada para ser LL(1); cada no-terminal se decide por un solo token de lookahead. Se implementa con un método por no-terminal — alineado con el requisito de hacer todo a mano.
- Implementación: `morselang/parser.py`.
- Ejemplo de árbol: `python main.py examples/hola.morse --ast`.

## 4. Tabla de símbolos

- Información almacenada: tipo, valor, línea de declaración.
- Estructura: hashmap (`dict` de Python) — ver `morselang/symbol_table.py`.
- Ejemplo de uso: durante la compilación de `factorial.morse` la tabla acumula `N:NUM=5`, `R:NUM=1`, y se actualiza en cada iteración del `MIENTRAS`.

## 5. Análisis semántico

- Reglas: variable declarada antes de usarse, no redeclaración, tipos compatibles, condición de SI/MIENTRAS debe ser BOOL, división por literal cero rechazada en compilación.
- Errores detectados: ver `examples/error_*.morse`.
- Ejemplos:
  - `error_no_declarada.morse` — usa `Z` sin declararla.
  - `error_redeclaracion.morse` — declara `X` dos veces.
  - `error_division_cero.morse` — divide por literal `0`.

## 6. Síntesis — intérprete + ElevenLabs

- Intérprete tree-walking: `morselang/interpreter.py`. Recorre el AST, mantiene un `SymbolTable` para las variables, y captura cada `MOSTRAR` en `interp.output`.
- TTS con ElevenLabs: `morselang/tts.py`. Al ejecutar con `--tts`, la salida acumulada se manda a la API de ElevenLabs y se guarda como `output.mp3`.
- Ejemplo: `python main.py examples/factorial.morse --tts` ejecuta, imprime `120` en consola y genera el audio narrando "ciento veinte".

## 7. Uso de IA

Ver `docs/uso_ia.md`.
