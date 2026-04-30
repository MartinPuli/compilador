"""Static reference text consumed by the TP Inspector page.

Keeping the prose here (instead of inline in the Streamlit page file)
makes it easy to edit the documentation without touching UI code.
"""

ALFABETO = (
    "Σ = { '.', '-', ' ', '/', '\\n', '\"' }\n"
    "Letras y dígitos se forman con secuencias de '.' y '-' separadas por\n"
    "un espacio. Las palabras (tokens) se separan con '/' o tres espacios."
)

EBNF = """programa     ::= { sentencia } ;
sentencia    ::= declaracion
              | asignacion
              | mostrar
              | si
              | mientras ;
declaracion  ::= "VAR" identificador "ASIG" expresion "\\n" ;
asignacion   ::= identificador "ASIG" expresion "\\n" ;
mostrar      ::= "MOSTRAR" expresion "\\n" ;
si           ::= "SI" expresion "\\n" { sentencia } [ "SINO" "\\n" { sentencia } ] "FIN" "\\n" ;
mientras     ::= "MIENTRAS" expresion "\\n" { sentencia } "FIN" "\\n" ;

expresion    ::= comparacion ;
comparacion  ::= aritmetica [ ("IGUAL"|"DIST"|"MEN"|"MAY") aritmetica ] ;
aritmetica   ::= termino { ("MAS"|"MENOS") termino } ;
termino      ::= factor { ("POR"|"DIV") factor } ;
factor       ::= numero | texto | "VERDADERO" | "FALSO" | identificador
              | "(" expresion ")" ;
"""

DERIVACION = """sentencia ⇒ declaracion
         ⇒ "VAR" identificador "ASIG" expresion
         ⇒ "VAR" "X" "ASIG" expresion
         ⇒ "VAR" "X" "ASIG" comparacion
         ⇒ "VAR" "X" "ASIG" aritmetica
         ⇒ "VAR" "X" "ASIG" termino
         ⇒ "VAR" "X" "ASIG" factor
         ⇒ "VAR" "X" "ASIG" numero
         ⇒ "VAR" "X" "ASIG" "10"
"""

AFD_ASCII = """          ┌────────┐
   start ─▶│   S0   │── '.' or '-' ──▶┐
          └────────┘                  ▼
                                   ┌────────┐
                                   │   S1   │── '.' or '-' ──▶ S1
                                   │ accum  │
                                   └────────┘
                                   │  ' '   │  '/' / '\\n' / '\"'
                                   ▼         ▼
                              emit letter   emit separator / start string
"""

PARSER_JUSTIFICATION = (
    "Recursivo descendente, LL(1). La gramática se diseñó para que cada\n"
    "no-terminal se decida con un solo token de lookahead: las sentencias se\n"
    "discriminan por su keyword inicial (VAR/MOSTRAR/SI/MIENTRAS) o por un\n"
    "IDENT en el caso de la asignación. Las expresiones usan precedencia por\n"
    "niveles (comparación → aditivo → multiplicativo → factor) para evitar\n"
    "recursión por izquierda. Es el método más didáctico para un TP y se\n"
    "implementa en pocas líneas por no-terminal — alineado con el requisito\n"
    "de hacer todo a mano."
)

SYMBOL_TABLE_DESC = (
    "Hashmap (`dict` de Python) con clave = nombre de la variable y valor =\n"
    "`SymbolInfo(tipo, valor, linea_declaracion)`. Métodos: declarar, asignar,\n"
    "consultar, existe, snapshot. Un único ámbito global (sin funciones)."
)
