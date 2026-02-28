KEYWORDS = {
    "class","public","static","void","int","double","String",
    "if","else","for","while","return","new","boolean","char",
}

OPERADORES_DOBLES = {"==","!=","<=",">=","++","--","+=","-=","*=","/="}
SIMBOLOS = "{}();,.[]"

def es_letra(c):
    return c.isalpha() or c == "_"

def es_numero(c):
    return c.isdigit()

def analizador_lexico(codigo):

    tokens = []
    errores = []
    tabla_simbolos = {}

    i = 0
    linea = 1
    columna = 1

    while i < len(codigo):
        c = codigo[i]

        if c == "\n":
            linea += 1
            columna = 1
            i += 1
            continue

        if c.isspace():
            columna += 1
            i += 1
            continue

        if codigo[i:i+2] == "//":
            while i < len(codigo) and codigo[i] != "\n":
                i += 1
            continue

        if codigo[i:i+2] == "/*":
            i += 2
            while i < len(codigo) and codigo[i:i+2] != "*/":
                if codigo[i] == "\n":
                    linea += 1
                    columna = 1
                i += 1
            i += 2
            continue

        if es_letra(c):
            inicio = i
            col = columna

            while i < len(codigo) and (es_letra(codigo[i]) or es_numero(codigo[i])):
                i += 1

            lexema = codigo[inicio:i]
            tipo = "KEYWORD" if lexema in KEYWORDS else "IDENTIFICADOR"

            tokens.append((tipo, lexema, linea, col))

            if tipo == "IDENTIFICADOR": 
                if lexema not in tabla_simbolos:
                    tabla_simbolos[lexema] = {
                        "tipo": "ID",
                        "linea": linea
                    }

            columna += len(lexema)
            continue

        if es_numero(c):
            inicio = i
            col = columna

            while i < len(codigo) and es_numero(codigo[i]):
                i += 1

            if i < len(codigo) and codigo[i] == ".":
                i += 1
                while i < len(codigo) and es_numero(codigo[i]):
                    i += 1

            lexema = codigo[inicio:i]
            tokens.append(("NUMERO", lexema, linea, col))
            columna += len(lexema)
            continue

        if c == '"':
            inicio = i
            col = columna
            i += 1

            while i < len(codigo) and codigo[i] != '"':
                if codigo[i] == "\n":
                    linea += 1
                i += 1

            i += 1
            lexema = codigo[inicio:i]

            tokens.append(("STRING", lexema, linea, col))
            columna += len(lexema)
            continue

        if codigo[i:i+2] in OPERADORES_DOBLES:
            tokens.append(("OPERADOR", codigo[i:i+2], linea, columna))
            i += 2
            columna += 2
            continue

        if c in "+-*/=<>!":
            tokens.append(("OPERADOR", c, linea, columna))
            i += 1
            columna += 1
            continue

        if c in SIMBOLOS:
            tokens.append(("SIMBOLO", c, linea, columna))
            i += 1
            columna += 1
            continue

        errores.append(("ERROR", c, linea, columna))
        i += 1
        columna += 1

    return tokens, errores, tabla_simbolos