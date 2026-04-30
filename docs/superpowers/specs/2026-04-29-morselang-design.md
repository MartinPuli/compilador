# MorseLang — Diseño

**Fecha:** 2026-04-29
**Modalidad:** TP individual — Lenguajes Formales y Compiladores
**Repo:** `c:/Users/marti/Documents/compilador`

## 1. Resumen

MorseLang es un lenguaje de programación imperativo de propósito general (nivel intermedio) **cuyo código fuente se escribe en código Morse**. El compilador, escrito a mano en Python 3, decodifica el Morse, tokeniza, parsea, valida tipos y ejecuta el programa. Como fase de síntesis, la salida del programa se narra con voz humana usando la API de ElevenLabs.

El diseño cubre las 7 partes obligatorias del TP:

| Parte | Componente |
|---|---|
| 1 — Definición del lenguaje | Alfabeto Morse, tokens, gramática EBNF, ejemplo de derivación |
| 2 — Análisis léxico | Codec Morse + autómata AFD, tokenizador escrito a mano |
| 3 — Análisis sintáctico | Parser recursivo descendente (LL(1)) que construye un AST |
| 4 — Tabla de símbolos | Hashmap con tipo, valor, línea de declaración y ámbito |
| 5 — Análisis semántico | Validación de tipos, declaración previa, redeclaración, división por cero |
| 6 — Síntesis | Intérprete tree-walking + cliente ElevenLabs (text-to-speech) |
| 7 — Uso de IA | Bitácora de prompts, código generado, errores detectados, correcciones |

## 2. Definición del lenguaje (Parte 1)

### 2.1 Alfabeto

El alfabeto del código fuente es:

```
Σ = { '.', '-', ' ', '/', '\n', '"' } ∪ { dígitos ASCII para identificación de líneas en errores }
```

- `.` y `-` son los componentes Morse atómicos
- ` ` (un espacio) separa letras dentro de una palabra
- `/` (o tres espacios consecutivos) separa palabras/tokens
- `\n` separa instrucciones
- `"` delimita literales de texto (su contenido es Morse)

### 2.2 Tabla Morse (referencia)

Letras A–Z, dígitos 0–9 según el estándar ITU. Ej: `A=.- B=-... C=-.-. … 0=----- 1=.---- … 9=----.`.

### 2.3 Categorías de tokens (alto nivel)

| Categoría | Ejemplo (decodificado) | Notas |
|---|---|---|
| Palabra clave | `VAR`, `MOSTRAR`, `SI`, `SINO`, `MIENTRAS`, `FIN`, `VERDADERO`, `FALSO` | Palabras reservadas |
| Identificador | `X`, `CONTADOR`, `TOTAL` | Letras A–Z (mayúsculas), longitud ≥ 1 |
| Número | `42`, `1024` | Secuencia de dígitos Morse |
| Texto | `"... .- .-.. ..- -.. ---"` | Comillas ASCII, contenido Morse |
| Operador | `MAS`, `MENOS`, `POR`, `DIV`, `IGUAL`, `DIST`, `MEN`, `MAY`, `ASIG` | Palabras reservadas (todas en Morse). `ASIG` cumple el rol de `=` (asignación). |
| Separador | `/` o triple espacio | Implícito en el flujo del lexer |
| Fin de línea | `\n` | Termina una sentencia |

> **Nota de diseño:** se usan operadores como palabras (`MAS`, `MENOS`, etc.) en vez de símbolos, porque `+`, `-`, `*`, `/` no son representables limpiamente en Morse sin solapamiento con dígitos/separadores. Esto simplifica el autómata.

### 2.4 Gramática (EBNF)

```ebnf
programa     ::= { sentencia } ;
sentencia    ::= declaracion
               | asignacion
               | mostrar
               | si
               | mientras ;
declaracion  ::= "VAR" identificador "ASIG" expresion "\n" ;
asignacion   ::= identificador "ASIG" expresion "\n" ;
mostrar      ::= "MOSTRAR" expresion "\n" ;
si           ::= "SI" expresion "\n" { sentencia } [ "SINO" "\n" { sentencia } ] "FIN" "\n" ;
mientras     ::= "MIENTRAS" expresion "\n" { sentencia } "FIN" "\n" ;

expresion    ::= comparacion ;
comparacion  ::= aritmetica [ ( "IGUAL" | "DIST" | "MEN" | "MAY" ) aritmetica ] ;
aritmetica   ::= termino { ( "MAS" | "MENOS" ) termino } ;
termino      ::= factor { ( "POR" | "DIV" ) factor } ;
factor       ::= numero
               | texto
               | "VERDADERO"
               | "FALSO"
               | identificador
               | "(" expresion ")" ;

identificador ::= letra { letra } ;
numero        ::= digito { digito } ;
texto         ::= '"' { letra | digito | espacio_intra } '"' ;
```

### 2.5 Ejemplo de derivación

Programa fuente (Morse, separadores en `/`):

```
...- .- .-.   /   -..-   /   ASIG   /   .---- -----
-- --- ... - .-. .- .-.   /   -..-
```

Decodificado a texto (paso intermedio del lexer):

```
VAR X ASIG 10
MOSTRAR X
```

Derivación de la primera sentencia:

```
sentencia ⇒ declaracion
          ⇒ "VAR" identificador "ASIG" expresion "\n"
          ⇒ "VAR" "X" "ASIG" expresion "\n"
          ⇒ "VAR" "X" "ASIG" comparacion "\n"
          ⇒ "VAR" "X" "ASIG" aritmetica "\n"
          ⇒ "VAR" "X" "ASIG" termino "\n"
          ⇒ "VAR" "X" "ASIG" factor "\n"
          ⇒ "VAR" "X" "ASIG" numero "\n"
          ⇒ "VAR" "X" "ASIG" "10" "\n"
```

## 3. Análisis léxico (Parte 2)

### 3.1 Estrategia en dos pasos

1. **Decodificador Morse** — autómata AFD que recorre el texto carácter por carácter, acumula `.`/`-`, al ver separador emite la letra/dígito decodificado a un buffer de texto.
2. **Tokenizador clásico** — sobre ese buffer de texto reconoce keywords, identificadores, números y literales.

Esto separa responsabilidades y el autómata de Morse queda bien acotado para presentarlo en el informe.

### 3.2 Expresiones regulares (sobre el texto decodificado)

| Token | Regex |
|---|---|
| KEYWORD | `VAR\|MOSTRAR\|SI\|SINO\|MIENTRAS\|FIN\|VERDADERO\|FALSO` |
| OPERATOR | `MAS\|MENOS\|POR\|DIV\|IGUAL\|DIST\|MEN\|MAY\|ASIG` |
| IDENT | `[A-Z][A-Z]*` |
| NUMBER | `[0-9]+` |
| STRING | `"[^"]*"` (su contenido se redecodifica) |
| NEWLINE | `\n` |

### 3.3 Autómata Morse (AFD)

Estados: `S0` (inicio), `S_dot_dash` (acumulando símbolos), `S_sep_letter`, `S_sep_word`, `S_string` (dentro de comillas).
Transiciones documentadas en el informe con diagrama. Salida: secuencia de letras/dígitos + separadores de palabra/línea.

### 3.4 Implementación

`morselang/morse.py` — funciones puras `morse_a_texto(s)` y `texto_a_morse(s)` (esta última solo para tests/helpers).
`morselang/lexer.py` — clase `Lexer` con método `tokenize() -> List[Token]`.

## 4. Análisis sintáctico (Parte 3)

### 4.1 Tipo de parser

**Recursivo descendente, LL(1)**, escrito a mano.

**Justificación:**
- La gramática se diseñó para ser LL(1) (cada no-terminal se decide por un solo token de lookahead).
- Es el método más didáctico y se implementa en pocas líneas por no-terminal — alineado con el requisito "todo a mano".
- No hay recursión por izquierda problemática (las reglas iterativas usan `{ … }` que se traduce a un loop `while`).

### 4.2 Implementación

`morselang/parser.py` — clase `Parser` con un método por no-terminal: `parse_programa()`, `parse_sentencia()`, `parse_expresion()`, etc.
Construye nodos definidos en `morselang/ast_nodes.py`.

### 4.3 Ejemplo de AST

Para `VAR X ASIG 10 + 5`:

```
Programa
└── Declaracion(nombre='X')
    └── BinOp('MAS')
        ├── Numero(10)
        └── Numero(5)
```

## 5. Tabla de símbolos (Parte 4)

### 5.1 Información almacenada

Cada entrada: `{ nombre, tipo, valor, linea_declaracion, ambito }`.

### 5.2 Estructura

`dict` de Python (hashmap). En esta versión hay **un solo ámbito global** (no funciones definibles en el nivel medio).
Métodos: `declarar(nombre, tipo, linea)`, `asignar(nombre, valor)`, `consultar(nombre)`, `existe(nombre)`.

### 5.3 Ejemplo durante la compilación

```
1: VAR X ASIG 10
2: VAR Y ASIG X MAS 5
3: MOSTRAR Y
```

| Línea | Acción | Estado de la tabla |
|---|---|---|
| 1 | declarar `X:NUM=10` | `{X: {tipo:NUM, valor:10, linea:1}}` |
| 2 | declarar `Y:NUM`, evalúa `X+5=15`, asigna | `{X: …, Y: {tipo:NUM, valor:15, linea:2}}` |
| 3 | consulta `Y` para imprimir | (sin cambios) |

## 6. Análisis semántico (Parte 5)

### 6.1 Reglas

1. Una variable debe declararse antes de usarse.
2. No se puede redeclarar una variable en el mismo ámbito.
3. En `ASIG`, el tipo del lado derecho debe coincidir con el de la variable (o ser convertible — solo `NUM`).
4. Operadores aritméticos requieren ambos operandos `NUM`.
5. Operadores de comparación requieren operandos del mismo tipo.
6. Condición de `SI`/`MIENTRAS` debe ser `BOOL` (resultado de comparación o literal).
7. División por cero es error semántico cuando el divisor es literal `0`; en runtime, error de ejecución.

### 6.2 Errores reportados

`SemanticError` con mensaje claro y número de línea. Ej:
- `Línea 3: variable 'Z' no declarada`
- `Línea 5: redeclaración de 'X' (declarada originalmente en línea 1)`
- `Línea 7: tipo incompatible — esperado NUM, recibido TEXTO`
- `Línea 9: división por cero`

### 6.3 Ejemplos ilustrativos

Programa con error (TEXTO + NUM):

```
VAR S ASIG "..."     ; S es TEXTO
VAR N ASIG S MAS 1   ; ERROR semántico
```

## 7. Síntesis — intérprete + ElevenLabs (Parte 6)

### 7.1 Intérprete

`morselang/interpreter.py` — `Interpreter` recorre el AST con visitor pattern. Mantiene la tabla de símbolos en runtime. `MOSTRAR` escribe a `stdout` y a un buffer interno.

### 7.2 Cliente ElevenLabs

`morselang/tts.py` — al finalizar la ejecución, si la CLI se invoca con `--tts`, manda el buffer acumulado a la API de ElevenLabs y guarda `output.mp3`.

- Endpoint: `text-to-speech/{voice_id}` (SDK oficial de Python)
- Voz: configurable via env var `ELEVENLABS_VOICE_ID` (default a una voz en español)
- API key: env var `ELEVENLABS_API_KEY`
- Si no hay API key configurada, el `--tts` falla con mensaje claro pero el resto del compilador funciona normalmente.

### 7.3 CLI

```
python main.py archivo.morse           # solo ejecuta
python main.py archivo.morse --tts     # ejecuta + narra con ElevenLabs
python main.py archivo.morse --ast     # imprime el AST (debug)
python main.py archivo.morse --tokens  # imprime los tokens (debug)
```

## 8. Uso de IA (Parte 7)

Mantenemos `docs/uso_ia.md` durante el desarrollo, registrando:

- Herramienta(s) usada(s) (Claude Code).
- Prompts relevantes — capturas o transcripciones.
- Componentes generados con asistencia (lexer, parser, etc.).
- Errores detectados en lo que produjo la IA.
- Correcciones aplicadas a mano.

Este documento es la fuente para la sección 7 del informe final.

## 9. Estructura del proyecto

```
compilador/
├── morselang/
│   ├── __init__.py
│   ├── morse.py          # Codec Morse ↔ texto
│   ├── lexer.py          # Tokenizador
│   ├── ast_nodes.py      # Definición de nodos AST
│   ├── parser.py         # Parser recursivo descendente
│   ├── symbol_table.py   # Tabla de símbolos
│   ├── semantic.py       # Análisis semántico
│   ├── interpreter.py    # Intérprete
│   └── tts.py            # Cliente ElevenLabs
├── examples/
│   ├── hola.morse
│   ├── factorial.morse
│   └── fizzbuzz.morse
├── tests/
│   ├── test_morse.py
│   ├── test_lexer.py
│   ├── test_parser.py
│   ├── test_semantic.py
│   └── test_interpreter.py
├── docs/
│   ├── superpowers/specs/2026-04-29-morselang-design.md   # este archivo
│   ├── informe.md        # borrador del informe en PDF
│   └── uso_ia.md         # bitácora Parte 7
├── main.py               # CLI
├── requirements.txt      # elevenlabs, pytest
├── .env.example          # ELEVENLABS_API_KEY=...
└── README.md
```

## 10. Tecnología

- **Lenguaje:** Python 3.11+
- **Dependencias:** `elevenlabs` (SDK oficial), `pytest` (tests)
- **Sin parser generators** — todo a mano según consigna del TP.

## 11. Programas de ejemplo previstos

| Archivo | Demuestra |
|---|---|
| `hola.morse` | `MOSTRAR` con texto literal |
| `factorial.morse` | `MIENTRAS`, aritmética, asignación |
| `fizzbuzz.morse` | `SI`/`SINO`, módulo (si lo agregamos), comparaciones |
| `error_*.morse` | Programas con errores deliberados (uno por categoría semántica) |

## 12. Plan de testing

- `pytest` por módulo, con archivos de fixtures Morse.
- Cada parte del compilador testeable en aislamiento (lexer, parser, etc.) gracias a interfaces claras entre módulos.
- Tests end-to-end que ejecutan los `examples/` y comparan salida esperada.

## 13. Fuera de alcance (explícitamente no se hace)

- Funciones definibles por el usuario.
- Arrays / listas.
- Tipos `float` / decimales.
- Optimización de código intermedio.
- Generación de bytecode o ejecutable.
- STT (audio → Morse) — solo TTS de salida.
