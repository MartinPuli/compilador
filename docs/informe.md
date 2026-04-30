# TP Integrador — Compilador MorseLang

**Lenguaje:** MorseLang — lenguaje imperativo cuyo código fuente se escribe en código Morse.
**Implementación:** Python 3.12, todo a mano (sin parser generators), 74 tests automatizados.

> Para una vista interactiva de cada Parte, abrir el Studio y usar la pestaña **TP Inspector**:
> `streamlit run studio/app.py`.

## 1. Definición del lenguaje

### Descripción informal

MorseLang es un lenguaje imperativo de propósito general (nivel intermedio). Soporta variables tipadas (NUM, TEXTO, BOOL), aritmética entera, comparaciones, `SI/SINO`, `MIENTRAS` y `MOSTRAR`. Su rasgo distintivo es que el código fuente se escribe en código Morse: cada keyword, identificador, número y string es una secuencia de `.` y `-`.

### Alfabeto

```
Σ = { '.', '-', ' ', '/', '\n', '"' }
```

### Tokens

| Categoría | Ejemplos |
|---|---|
| Keyword | VAR, MOSTRAR, SI, SINO, MIENTRAS, FIN, VERDADERO, FALSO |
| Operador (palabra Morse) | MAS, MENOS, POR, DIV, IGUAL, DIST, MEN, MAY, ASIG |
| Identificador | A–Z, ≥1 letra |
| Número | secuencia de dígitos Morse |
| Texto | `"..."` con contenido Morse |
| Estructural | NEWLINE, EOF |

### Gramática (EBNF)

```ebnf
programa     ::= { sentencia } ;
sentencia    ::= declaracion | asignacion | mostrar | si | mientras ;
declaracion  ::= "VAR" identificador "ASIG" expresion "\n" ;
asignacion   ::= identificador "ASIG" expresion "\n" ;
mostrar      ::= "MOSTRAR" expresion "\n" ;
si           ::= "SI" expresion "\n" { sentencia } [ "SINO" "\n" { sentencia } ] "FIN" "\n" ;
mientras     ::= "MIENTRAS" expresion "\n" { sentencia } "FIN" "\n" ;

expresion    ::= comparacion ;
comparacion  ::= aritmetica [ ("IGUAL"|"DIST"|"MEN"|"MAY") aritmetica ] ;
aritmetica   ::= termino { ("MAS"|"MENOS") termino } ;
termino      ::= factor { ("POR"|"DIV") factor } ;
factor       ::= numero | texto | "VERDADERO" | "FALSO" | identificador
              | "(" expresion ")" ;
```

### Ejemplo de derivación

Para `VAR X ASIG 10`:

```
sentencia ⇒ declaracion
         ⇒ "VAR" identificador "ASIG" expresion
         ⇒ "VAR" "X" "ASIG" numero
         ⇒ "VAR" "X" "ASIG" "10"
```

## 2. Análisis léxico

### Estrategia

Dos pasos: (1) decodificación Morse → texto, (2) clasificación del texto en tokens. La separación mantiene el AFD de la primera fase pequeño y testeable.

### Expresiones regulares (sobre el texto decodificado)

| Token | Regex |
|---|---|
| KEYWORD/OPERATOR | `VAR\|MOSTRAR\|SI\|...\|ASIG` |
| IDENT | `[A-Z]+` |
| NUMBER | `[0-9]+` |
| STRING | `"[^"]*"` |
| NEWLINE | `\n` |

### AFD del decodificador Morse

```
          ┌────────┐
   start ─▶│   S0   │── '.' or '-' ──▶┐
          └────────┘                  ▼
                                   ┌────────┐
                                   │   S1   │── '.' or '-' ──▶ S1
                                   │ accum  │
                                   └────────┘
                                   │  ' '   │  '/' / '\n' / '"'
                                   ▼         ▼
                              emit letter   emit separator / start string
```

Implementación: `morselang/lexer.py`. Visualización en vivo: TP Inspector → pestaña 2.

## 3. Análisis sintáctico

### Tipo

Recursivo descendente, **LL(1)**.

### Justificación

Cada no-terminal se decide con un único token de lookahead. Las sentencias se discriminan por keyword inicial (VAR/MOSTRAR/SI/MIENTRAS) o IDENT (asignación). Las expresiones usan precedencia por niveles (`comparacion` → `aritmetica` → `termino` → `factor`) para evitar recursión por izquierda. Es el método más didáctico para un TP y se implementa en pocas líneas por no-terminal — alineado con el requisito de hacer todo a mano.

### Implementación

`morselang/parser.py`. Construye un AST de dataclasses definidas en `morselang/ast_nodes.py`.

### Ejemplo

Para `VAR X ASIG 10 MAS 5`:

```
Programa
└── Declaracion(name='X')
    └── BinOp('MAS')
        ├── NumeroLit(10)
        └── NumeroLit(5)
```

Visualización en vivo: TP Inspector → pestaña 3.

## 4. Tabla de símbolos

### Estructura

`dict` con clave = nombre de la variable y valor = `SymbolInfo(tipo, valor, linea_declaracion)`. Métodos: `declarar`, `asignar`, `consultar`, `existe`, `snapshot`. Un único ámbito global.

### Estrategia

- `declarar(name, tipo, line)` — falla si ya existe.
- `asignar(name, valor)` — falla si no fue declarada.
- `consultar(name)` — falla si no existe.

### Ejemplo de uso (factorial.morse)

| Línea | Tabla |
|---|---|
| 1 (VAR N=5)  | `{N: NUM=5}` |
| 2 (VAR R=1)  | `{N: NUM=5, R: NUM=1}` |
| iter 1       | `{N: NUM=4, R: NUM=5}` |
| iter 2       | `{N: NUM=3, R: NUM=20}` |
| iter 3       | `{N: NUM=2, R: NUM=60}` |
| iter 4       | `{N: NUM=1, R: NUM=120}` |
| iter 5       | `{N: NUM=0, R: NUM=120}` |
| 7 (MOSTRAR R)| `{N: NUM=0, R: NUM=120}` → imprime 120 |

Visualización en vivo: TP Inspector → pestaña 4.

## 5. Análisis semántico

### Reglas

1. Variable declarada antes de usarse.
2. No redeclaración.
3. Aritmética requiere ambos operandos NUM.
4. Comparación requiere operandos del mismo tipo.
5. Condición de SI / MIENTRAS debe ser BOOL.
6. División por literal `0` rechazada en compilación.
7. División por variable `0` se detecta en runtime (`RuntimeError_`).

### Errores

| Programa | Mensaje |
|---|---|
| `error_no_declarada.morse` | `Línea 1: variable 'Z' no declarada` |
| `error_redeclaracion.morse` | `Línea 2: redeclaración de 'X' (declarada originalmente en línea 1)` |
| `error_division_cero.morse` | `Línea 1: división por cero` |

Visualización en vivo: TP Inspector → pestaña 5.

## 6. Síntesis — intérprete + ElevenLabs

Se eligió **intérprete tree-walking** como fase de síntesis (Parte 6 del TP — opción "Intérprete del lenguaje"). El intérprete recorre el AST, mantiene una tabla de símbolos en runtime y captura cada `MOSTRAR` en `interp.output`.

Como cierre vistoso, la salida acumulada se envía a la **API de ElevenLabs** para producir un `output.mp3` que narra el resultado con voz humana en español.

```
archivo.morse → Lexer → Parser → AST → Semántico → Intérprete → output.mp3
```

CLI:

```bash
python main.py examples/factorial.morse        # solo ejecuta
python main.py examples/factorial.morse --tts  # + narración ElevenLabs
```

Studio:

```bash
streamlit run studio/app.py
```

## 7. Uso de IA

Ver `docs/uso_ia.md`.
