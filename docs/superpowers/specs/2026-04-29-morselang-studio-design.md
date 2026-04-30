# MorseLang Studio — Diseño

**Fecha:** 2026-04-29
**Repo:** `c:/Users/marti/Documents/compilador`
**Branch base:** `feat/morselang-implementation` (compilador ya implementado)

## 1. Resumen

Construir una interfaz visual sobre el compilador MorseLang existente, agregar un decoder de audio Morse (audio → código fuente), enriquecer la documentación, y publicar un skill de Claude (`SKILL.md`) que enseña a Claude a usar el compilador en futuras sesiones.

Cuatro entregas:

1. **`MorseLang Studio`** — app web Streamlit con editor + audio decoder + visor de cada Parte del TP.
2. **`morselang/audio.py`** — decoder Morse a partir de audio (DSP escrito a mano con numpy/scipy).
3. **`docs/informe.md` enriquecido** — secciones completas con diagramas, ejemplos, snapshots.
4. **`.claude/skills/morselang-compiler/SKILL.md`** — skill instalable de Claude.

El compilador subyacente no se modifica salvo para exponer hooks de instrumentación que el Studio necesita (tabla de símbolos en vivo, AST en JSON).

## 2. Stack y dependencias

| Componente | Lib |
|---|---|
| UI web | `streamlit>=1.30` |
| Audio mic | `st.audio_input` (built-in en Streamlit ≥1.31) |
| Audio decoder | `numpy`, `scipy.signal` |
| Visualización AST | `graphviz` (Python wrapper) — fallback a texto si no hay binario instalado |
| Tests | `pytest` (existente) |

Se agregan a `requirements.txt`: `streamlit`, `numpy`, `scipy`, `graphviz`.

## 3. Studio — layout y comportamiento

### 3.1 Páginas (sidebar)

1. **Editor**
2. **Audio → Morse**
3. **TP Inspector**
4. **Ayuda**

### 3.2 Página "Editor"

- `st.text_area` (alto = 280 px, fuente monoespaciada) para el código fuente.
- Botonera horizontal: `▶ Ejecutar` · `🔍 Tokens` · `🌳 AST` · `🔊 TTS`.
- Panel "Resultado" debajo:
  - Si hay error: caja roja con tipo (`Léxico`/`Sintáctico`/`Semántico`/`Ejecución`) + mensaje + línea.
  - Si OK: lista de líneas que el programa imprimió.
- Panel "Tabla de símbolos" (colapsable): se llena después de cada ejecución exitosa con el snapshot final.
- Selector "Cargar ejemplo" arriba a la derecha que carga `examples/*.morse`.
- `🔊 TTS` exige `ELEVENLABS_API_KEY` en `.env`. Si falta, muestra warning explicativo.

### 3.3 Página "Audio → Morse"

- Componente de captura: `st.audio_input("Grabá Morse")` (browser mic) **o** `st.file_uploader` (.wav).
- Slider opcional "WPM esperado" (5–40, default = autodetect).
- Botón `🔍 Decodificar`:
  - Llama a `morselang.audio.decode_audio_to_morse(samples, sample_rate, wpm=None)`.
  - Muestra el string Morse decodificado en un `st.code(...)`.
  - Muestra un panel de "Diagnóstico DSP": dot-length detectado, pulsos detectados, gráfico de envolvente (`st.line_chart` con la envolvente y el threshold).
- Botón `→ Mandar al editor`: navega a la página "Editor" con el Morse pre-cargado.

### 3.4 Página "TP Inspector"

Una sección por cada Parte del TP, con anclas en la URL para navegación rápida:

#### Parte 1 — Definición del lenguaje

- Sección "Alfabeto" (contenido de la spec).
- Sección "Tokens" (tabla auto-generada desde `morselang.tokens.KEYWORDS`).
- Sección "Gramática EBNF" — `st.code(..., language="ebnf")` con la EBNF completa.
- Sección "Ejemplo de derivación" — derivación paso a paso del programa más simple.

#### Parte 2 — Análisis léxico

- Diagrama del AFD del decodificador Morse — generado con graphviz como SVG embebido (fallback: ASCII art).
- Trace en vivo: input box donde el usuario tipea Morse, debajo se muestra la secuencia tokens emitida con sus tipos.

#### Parte 3 — Análisis sintáctico

- Texto: tipo de parser elegido + justificación.
- Visor de AST: input → ejecuta lexer + parser → renderiza el AST como árbol graphviz.

#### Parte 4 — Tabla de símbolos

- Diagrama de la estructura (texto + descripción).
- Modo "step": ejecuta el programa del editor y muestra la tabla **al final de cada sentencia**, con un slider para navegar las iteraciones.

#### Parte 5 — Análisis semántico

- Galería de los 3 programas error (`examples/error_*.morse`): card por cada uno con el Morse, qué regla viola, y el mensaje que produce el compilador (calculado en vivo).

#### Parte 6 — Síntesis

- Texto explicando intérprete + ElevenLabs.
- Player embebido del último `output.mp3` generado.

#### Parte 7 — Uso de IA

- Render Markdown de `docs/uso_ia.md`.

### 3.5 Página "Ayuda"

- Tabla Morse completa (letras + dígitos).
- Tabla de keywords con su Morse al lado.
- Lista de operadores con su Morse.
- Tips de sintaxis (separadores, strings, comentarios — *no hay comentarios* en v1).

## 4. Decoder de audio (`morselang/audio.py`)

### 4.1 API pública

```python
def decode_audio_to_morse(
    samples: np.ndarray,
    sample_rate: int,
    *,
    wpm: float | None = None,
    target_freq_hz: float | None = None,
) -> AudioDecodeResult: ...

@dataclass
class AudioDecodeResult:
    morse: str                    # e.g. ".... --- .-.. .-"
    detected_wpm: float
    dot_length_ms: float
    envelope: np.ndarray          # for diagnostic plotting
    threshold: float
    pulses: list[tuple[bool, float]]   # (is_on, duration_ms)
```

### 4.2 Pipeline

1. **Mono + normalize:** si stereo, promedia canales; normaliza a [-1, 1].
2. **Bandpass opcional:** si `target_freq_hz` dado, filtro butterworth de 200 Hz alrededor (mejora SNR si el tono Morse es conocido). Default: skip.
3. **Envelope:** RMS móvil con ventana de 10 ms (`scipy.signal`'s `convolve` con kernel rectangular).
4. **Threshold:** Otsu's method sobre la envolvente (binariza 0/1 en `is_on`).
5. **Run-length encoding** de la secuencia binaria → lista de `(is_on, duration_samples)`.
6. **Auto-detect dot length:** mediana de las duraciones de pulsos `on` cortos (cuartil inferior).
7. **Clasificar pulsos `on`:** ≤ 1.5 × dot ⇒ `.`, > 1.5 × dot ⇒ `-`.
8. **Clasificar silencios `off`:** ≤ 1.5 × dot ⇒ separador intra-letra (nada), 2–4 × dot ⇒ `' '` (separador de letras), ≥ 4 × dot ⇒ `'   '` (separador de palabras del lexer).
9. **Calcular WPM:** `1200 / dot_length_ms` (estándar PARIS).
10. Retornar `AudioDecodeResult`.

Si el override de `wpm` se pasa, **no** se autodetecta — se usa `dot_length_ms = 1200 / wpm`.

### 4.3 Errores

- `AudioDecodeError` cuando: array vacío, todo silencio, o no se encontraron pulsos `on` distinguibles.

### 4.4 Tests (TDD)

`tests/test_audio.py` con fixtures sintéticas:

```python
def synth_morse_wav(morse: str, wpm: int = 20, freq: int = 600, sr: int = 16000) -> np.ndarray
```

Tests:

- `test_decode_simple_letter` — synth(".-", wpm=20) → `decode_audio_to_morse` devuelve `.-` y `detected_wpm` ≈ 20.
- `test_decode_word` — synth("... --- ...", wpm=15) → `... --- ...`.
- `test_decode_two_words` — synth(".- / -...", wpm=20) → contains both letters separated by triple-space.
- `test_decode_with_noise` — synth + ruido gaussiano (SNR=10dB) sigue funcionando.
- `test_decode_silent_raises` — todo ceros → `AudioDecodeError`.
- `test_decode_with_explicit_wpm` — override sí cambia la decisión cuando los timings están en el límite.

## 5. Hooks de instrumentación en el compilador

Mínimos cambios al código existente para que el Studio pueda ver el estado interno:

- `Interpreter.execute(program, on_step=None)` — opcional callback `on_step(stmt, symbol_table_snapshot)` después de cada sentencia. Compatibilidad: si no se pasa, comportamiento idéntico al actual.
- `Programa.to_dict()` y similares en cada nodo AST — serializa a `dict` JSON-friendly para renderear en graphviz.
- Sin cambios destructivos. Los tests existentes siguen verdes.

## 6. Documentación enriquecida (`docs/informe.md`)

Actualizar de skeleton a documento sustancial:

- §1 Alfabeto + tabla completa de tokens + gramática EBNF + ejemplo de derivación con árbol dibujado en ASCII.
- §2 Diagrama AFD en ASCII art (estados S0..S4 con transiciones), regex por token, link al código.
- §3 Justificación del parser, ejemplo de árbol generado para `factorial.morse`.
- §4 Estructura de la tabla, snapshot durante `factorial.morse`.
- §5 Tabla de los 6 errores con su mensaje exacto.
- §6 Secuencia: programa → AST → ejecución → audio. Capturas del Studio.
- §7 Apunta a `uso_ia.md` (que también se enriquece).

## 7. SKILL.md para Claude

Ubicación: `.claude/skills/morselang-compiler/SKILL.md`

Frontmatter:

```yaml
---
name: morselang-compiler
description: Use when working with the MorseLang compiler — writing or running .morse programs, decoding Morse from audio, opening the Studio UI, or asking how to use the CLI. Triggers on requests like "run this morse program", "open morselang studio", "how do I write X in morselang", or any mention of MorseLang / .morse files.
---
```

Contenido (en español):

- **Sintaxis del lenguaje:** keywords, operadores, separadores, strings.
- **Cómo correr un programa:** `python main.py archivo.morse [--tokens|--ast|--tts]`.
- **Cómo abrir el Studio:** `streamlit run studio/app.py`.
- **Tabla Morse de referencia:** letras y dígitos.
- **Tabla de keywords:** cada keyword del lenguaje con su Morse correspondiente.
- **Plantillas de programas:** "hola mundo", "factorial", "loop con condicional".
- **Errores comunes:** símbolos Morse inválidos, separadores faltantes.
- **Workflow para defender el TP:** mostrar Editor, mostrar AST, disparar errores semánticos, ejecutar con TTS, mostrar Audio → Morse.

Tamaño objetivo: ~150 líneas de markdown, todo concreto, sin TBDs.

## 8. Estructura final del repo

```
compilador/
├── morselang/
│   ├── ... (archivos existentes sin cambios destructivos)
│   └── audio.py                # NUEVO
├── studio/
│   ├── __init__.py             # NUEVO
│   ├── app.py                  # NUEVO — entry point Streamlit
│   ├── pages/                  # NUEVO — una página por archivo
│   │   ├── editor.py
│   │   ├── audio_morse.py
│   │   ├── tp_inspector.py
│   │   └── ayuda.py
│   └── components.py           # NUEVO — helpers compartidos
├── examples/                   # sin cambios
├── tests/
│   ├── ... (existentes)
│   ├── test_audio.py           # NUEVO
│   └── test_studio_smoke.py    # NUEVO — solo importa la app
├── docs/
│   ├── informe.md              # ENRIQUECIDO
│   ├── uso_ia.md               # ENRIQUECIDO
│   └── superpowers/...         # specs y plans
├── .claude/
│   └── skills/
│       └── morselang-compiler/
│           └── SKILL.md        # NUEVO
├── main.py                     # sin cambios
├── requirements.txt            # ACTUALIZADO (streamlit, numpy, scipy, graphviz)
└── README.md                   # ACTUALIZADO con sección "Studio"
```

## 9. Plan de testing

- **Audio decoder:** 6 tests con fixtures sintéticas (sin archivos binarios committeados — generados en runtime).
- **Studio:** test de smoke (`importlib`) que verifica que `studio.app` se importa sin errores y expone funciones helper. No se testea Streamlit en sí.
- **Compilador subyacente:** los 60 tests existentes siguen verdes.

Total esperado al final: ~67 tests.

## 10. Fuera de alcance

- Edición colaborativa multi-usuario.
- Persistencia (no se guarda nada en DB; el editor mantiene estado solo en sesión).
- Decodificación de audio en tiempo real (siempre se procesa la grabación completa al apretar Decodificar).
- Generación de bytecode o JIT (la fase de síntesis sigue siendo intérprete + TTS).
- Translator a Python — opcional, mencionado por separado si el usuario lo pide después.

## 11. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Streamlit cambia API entre versiones | Pin `streamlit>=1.30,<2.0` en `requirements.txt` |
| `st.audio_input` no disponible en versión instalada | Fallback automático a `st.file_uploader` |
| graphviz no instalado en el sistema | Fallback a representación textual del AST |
| Mic del navegador rechazado por permisos | Mostrar mensaje claro + ofrecer upload manual |
| Audio con SNR muy bajo no decodifica | Diagnóstico DSP visible al usuario para ajustar |

## 12. Cómo se demuestra al profe

1. Abrir Studio (`streamlit run studio/app.py`).
2. Ir a "TP Inspector" y recorrer Partes 1–7 mostrando lo que hace cada panel.
3. Volver al Editor, cargar `factorial.morse`, ejecutar.
4. Hacer click en `🔊 TTS` → escuchar el resultado.
5. Ir a "Audio → Morse", grabar el dictado de un programa con la voz/celular, decodificar, mandarlo al editor, ejecutar.
