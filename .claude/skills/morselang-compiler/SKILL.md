---
name: morselang-compiler
description: Use when working with the MorseLang compiler — writing or running .morse programs, decoding Morse from audio, opening the Studio UI, or asking how to use the CLI. Triggers on requests like "run this morse program", "open morselang studio", "how do I write X in morselang", or any mention of MorseLang / .morse files.
---

# MorseLang — Skill

MorseLang es un lenguaje de programación imperativo cuyo código fuente se escribe en código Morse. Este skill enseña a Claude cómo usar el compilador y el Studio que están en este repo.

## Sintaxis del lenguaje

Cada keyword, identificador, número y string se escribe en Morse. Letras de una palabra se separan con un espacio; palabras (tokens) se separan con `/` o tres espacios; sentencias con salto de línea.

### Keywords

| Texto | Morse |
|---|---|
| VAR | `...- .- .-.` |
| MOSTRAR | `-- --- ... - .-. .- .-.` |
| SI | `... ..` |
| SINO | `... .. -. ---` |
| MIENTRAS | `-- .. . -. - .-. .- ...` |
| FIN | `..-. .. -.` |
| VERDADERO | `...- . .-. -.. .- -.. . .-. ---` |
| FALSO | `..-. .- .-.. ... ---` |

### Operadores (palabras Morse, no símbolos)

| Texto | Morse | Significado |
|---|---|---|
| MAS | `-- .- ...` | + |
| MENOS | `-- . -. --- ...` | − |
| POR | `.--. --- .-.` | × |
| DIV | `-.. .. ...-` | ÷ (entera) |
| IGUAL | `.. --. ..- .- .-..` | == |
| DIST | `-.. .. ... -` | != |
| MEN | `-- . -.` | < |
| MAY | `-- .- -.--` | > |
| ASIG | `.- ... .. --.` | = (asignación) |

### Tabla Morse de referencia

```
A=.-     B=-...   C=-.-.   D=-..    E=.      F=..-.
G=--.    H=....   I=..     J=.---   K=-.-    L=.-..
M=--     N=-.     O=---    P=.--.   Q=--.-   R=.-.
S=...    T=-      U=..-    V=...-   W=.--    X=-..-
Y=-.--   Z=--..

0=-----  1=.----  2=..---  3=...--  4=....-
5=.....  6=-....  7=--...  8=---..  9=----.
```

### Strings

Entre `"..."`. El contenido es Morse. Para preservar espacios entre palabras dentro del string, usar **triple espacio o `/`** entre las palabras y espacio simple entre las letras de cada palabra:

```
-- --- ... - .-. .- .-. / ".... --- .-.. .-   -- ..- -. -.. ---"
       MOSTRAR             "HOLA   MUNDO"  → imprime "HOLA MUNDO"
```

## Cómo correr un programa

```bash
python main.py archivo.morse                # solo ejecuta
python main.py archivo.morse --tokens       # imprime el token stream
python main.py archivo.morse --ast          # imprime el AST
python main.py archivo.morse --tts          # ejecuta + narra con ElevenLabs
```

`--tts` requiere `ELEVENLABS_API_KEY` en `.env` (ver `.env.example`).

Códigos de salida:

- `0` — éxito
- `1` — error en alguna fase del compilador (léxico/sintáctico/semántico/runtime)
- `2` — archivo no encontrado

## MORSE.LAB (UI visual recomendada)

UI web hecha a mano (Flask + HTML/CSS/JS, estética CRT phosphor):

```bash
flask --app web.server run --port 5173
# → http://127.0.0.1:5173
```

Cuatro vistas:

- **Editor** — escribir / pegar código, ejecutar, ver tokens y AST.
- **Audio** — subir un `.wav` con beeps Morse, decodificarlo, mandarlo al editor.
- **Inspector** — las 7 partes del TP en vivo (alfabeto, EBNF, AFD, AST en vivo, snapshot de tabla por sentencia, galería de errores semánticos, etc.).
- **Ayuda** — tablas de Morse, keywords y operadores.

Alternativa Streamlit (más feo pero también funciona):

```bash
streamlit run studio/app.py
```

## Plantillas de programas

### Hola mundo

```
-- --- ... - .-. .- .-. / ".... --- .-.. .-   -- ..- -. -.. ---"
```

### Variable + aritmética

```
...- .- .-. / -..- / .- ... .. --. / .---- -----
...- .- .-. / -.-- / .- ... .. --. / -..- / -- .- ... / .....
-- --- ... - .-. .- .-. / -.--
```

### MIENTRAS con condición

```
...- .- .-. / .. / .- ... .. --. / -----
-- .. . -. - .-. .- ... / .. / -- . -. / ...--
-- --- ... - .-. .- .-. / ..
.. / .- ... .. --. / .. / -- .- ... / .----
..-. .. -.
```

## Errores comunes

| Síntoma | Causa frecuente |
|---|---|
| `Símbolo Morse inválido: '........'` | Secuencia de 8 puntos no es ninguna letra. |
| `token desconocido tras decodificar Morse: 'XYZ'` | Secuencia decodificada no es keyword/ident/número válido. |
| `literal de texto sin cerrar` | Falta el `"` de cierre. |
| `redeclaración de 'X'` | Hay dos `VAR X ASIG ...` en el mismo programa. |
| `la condición debe ser BOOL` | Pasaste un número o texto a `SI`/`MIENTRAS`. |

## Workflow para defender el TP

1. Abrir Studio (`streamlit run studio/app.py`).
2. **TP Inspector** → recorrer las 7 pestañas mostrando lo que hace cada una.
3. Volver al **Editor** → cargar `factorial.morse` desde el dropdown → `Ejecutar` → mostrar la salida `120`.
4. En el CLI generar el audio: `python main.py examples/factorial.morse --tts` → reproducir `output.mp3`.
5. **Audio → Morse** → grabar/subir un `.wav` → `Decodificar` → `Mandar al editor` → ejecutar.
6. Mostrar el repo: `morselang/` (compilador), `tests/` (74 tests verdes), `docs/informe.md`.
