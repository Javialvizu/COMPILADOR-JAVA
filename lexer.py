"""
COMPILADOR JAVA - Análisis Léxico, Sintáctico y Semántico

Gramática BNF/EBNF utilizada:

program -> class_declaration

class_declaration -> "class" ID "{" declarations "}"

declarations -> declaration declarations | ε

declaration -> type ID ";" | method_declaration

method_declaration -> "public" "static" "void" "main" "(" ")" "{" statements "}"

statements -> statement statements | ε

statement -> var_declaration | assignment | if_statement | while_statement | return_statement

var_declaration -> type ID "=" expression ";"

assignment -> ID "=" expression ";"

if_statement -> "if" "(" expression ")" "{" statements "}" else_part

else_part -> "else" "{" statements "}" | ε

while_statement -> "while" "(" expression ")" "{" statements "}"

return_statement -> "return" expression ";"

expression -> comparison

comparison -> additive (( ">" | "<" | ">=" | "<=" | "==" | "!=" ) additive)*

additive -> term (( "+" | "-" ) term)*

term -> factor (( "*" | "/" ) factor)*

factor -> ID | NUMERO | STRING | "(" expression ")"

type -> "int" | "double" | "String" | "boolean"

Expresiones regulares para tokens:
- Identificadores: [a-zA-Z_][a-zA-Z0-9_]*
- Números: [0-9]+(\\.[0-9]+)?
- Operadores: +, -, *, /, =, ==, !=, <, >, <=, >=, ++, --, +=, -=, *=, /=
- Símbolos: {, }, (, ), ;, ,, ., [, ]
- Palabras clave: class, public, static, void, int, double, String, if, else, for, while, return, new, boolean, char
"""

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

def es_letra(c):
    return c.isalpha() or c == "_"

def es_numero(c):
    return c.isdigit()

# Parser
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.errors = []

    def current_token(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def consume(self, expected_type=None, expected_value=None):
        token = self.current_token()
        if token:
            if (expected_type and token[0] != expected_type) or (expected_value and token[1] != expected_value):
                self.errors.append(f"SYN-001: Error sintáctico: esperado {expected_type or ''} {expected_value or ''}, encontrado {token[0]} {token[1]} en línea {token[2]}")
                # Error recovery: skip this token and continue
                self.pos += 1
                return None
            self.pos += 1
            return token
        self.errors.append("SYN-002: Error sintáctico: token inesperado al final")
        return None

    def parse_program(self):
        class_decl = self.parse_class_declaration()
        if not class_decl:
            return None
        return {"type": "Program", "class_decl": class_decl}

    def parse_class_declaration(self):
        self.consume("KEYWORD", "class")
        name_token = self.consume("IDENTIFICADOR")
        if not name_token:
            return None
        self.consume("SIMBOLO", "{")
        declarations = []
        max_iter = 100
        iter_count = 0
        while self.current_token() and self.current_token()[1] != "}" and iter_count < max_iter:
            decl = self.parse_declaration()
            if decl:
                declarations.append(decl)
            iter_count += 1
        if iter_count >= max_iter:
            self.errors.append("SYN-003: Posible bucle infinito en declaraciones de clase")
        self.consume("SIMBOLO", "}")
        return {"type": "ClassDeclaration", "name": name_token[1], "declarations": declarations}

    def parse_declaration(self):
        token = self.current_token()
        if token and token[0] == "KEYWORD" and token[1] in ["int", "double", "String", "boolean"]:
            var_type = self.consume("KEYWORD")[1]
            name_token = self.consume("IDENTIFICADOR")
            self.consume("SIMBOLO", ";")
            return {"type": "VariableDeclaration", "var_type": var_type, "name": name_token[1]}
        elif token and token[1] == "public":
            return self.parse_method_declaration()
        return None

    def parse_method_declaration(self):
        self.consume("KEYWORD", "public")
        self.consume("KEYWORD", "static")
        self.consume("KEYWORD", "void")
        name_token = self.consume("IDENTIFICADOR")
        self.consume("SIMBOLO", "(")
        self.consume("SIMBOLO", ")")
        self.consume("SIMBOLO", "{")
        statements = []
        max_iter = 100
        iter_count = 0
        while self.current_token() and self.current_token()[1] != "}" and iter_count < max_iter:
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
            iter_count += 1
        if iter_count >= max_iter:
            self.errors.append("SYN-003: Posible bucle infinito en statements del método")
        self.consume("SIMBOLO", "}")
        return {"type": "MethodDeclaration", "name": name_token[1], "statements": statements}

    def parse_statement(self):
        token = self.current_token()
        if token and token[0] == "KEYWORD" and token[1] in ["int", "double", "String", "boolean"]:
            var_type = self.consume("KEYWORD")[1]
            name_token = self.consume("IDENTIFICADOR")
            self.consume("OPERADOR", "=")
            expr = self.parse_expression()
            self.consume("SIMBOLO", ";")
            return {"type": "VariableDeclaration", "var_type": var_type, "name": name_token[1], "init": expr}
        elif token and token[0] == "IDENTIFICADOR":
            name = self.consume("IDENTIFICADOR")[1]
            self.consume("OPERADOR", "=")
            expr = self.parse_expression()
            self.consume("SIMBOLO", ";")
            return {"type": "Assignment", "name": name, "expr": expr}
        elif token and token[1] == "if":
            return self.parse_if_statement()
        elif token and token[1] == "while":
            return self.parse_while_statement()
        elif token and token[1] == "return":
            self.consume("KEYWORD", "return")
            expr = self.parse_expression()
            self.consume("SIMBOLO", ";")
            return {"type": "ReturnStatement", "expr": expr}
        return None

    def parse_if_statement(self):
        self.consume("KEYWORD", "if")
        self.consume("SIMBOLO", "(")
        condition = self.parse_expression()
        self.consume("SIMBOLO", ")")
        self.consume("SIMBOLO", "{")
        then_stmts = []
        max_iter = 50
        iter_count = 0
        while self.current_token() and self.current_token()[1] != "}" and iter_count < max_iter:
            stmt = self.parse_statement()
            if stmt:
                then_stmts.append(stmt)
            iter_count += 1
        if iter_count >= max_iter:
            self.errors.append("SYN-003: Posible bucle infinito en then statements")
        self.consume("SIMBOLO", "}")
        else_stmts = []
        if self.current_token() and self.current_token()[1] == "else":
            self.consume("KEYWORD", "else")
            self.consume("SIMBOLO", "{")
            iter_count = 0
            while self.current_token() and self.current_token()[1] != "}" and iter_count < max_iter:
                stmt = self.parse_statement()
                if stmt:
                    else_stmts.append(stmt)
                iter_count += 1
            if iter_count >= max_iter:
                self.errors.append("SYN-003: Posible bucle infinito en else statements")
            self.consume("SIMBOLO", "}")
        return {"type": "IfStatement", "condition": condition, "then_stmts": then_stmts, "else_stmts": else_stmts}

    def parse_while_statement(self):
        self.consume("KEYWORD", "while")
        self.consume("SIMBOLO", "(")
        condition = self.parse_expression()
        self.consume("SIMBOLO", ")")
        self.consume("SIMBOLO", "{")
        stmts = []
        max_iter = 50
        iter_count = 0
        while self.current_token() and self.current_token()[1] != "}" and iter_count < max_iter:
            stmt = self.parse_statement()
            if stmt:
                stmts.append(stmt)
            iter_count += 1
        if iter_count >= max_iter:
            self.errors.append("SYN-003: Posible bucle infinito en while statements")
        self.consume("SIMBOLO", "}")
        return {"type": "WhileStatement", "condition": condition, "stmts": stmts}

    def parse_expression(self):
        return self.parse_comparison()

    def parse_comparison(self):
        left = self.parse_additive()
        if self.current_token() and self.current_token()[1] in [">", "<", ">=", "<=", "==", "!="]:
            op = self.consume("OPERADOR")[1]
            right = self.parse_additive()
            left = {"type": "BinaryOp", "left": left, "op": op, "right": right}
        return left

    def parse_additive(self):
        left = self.parse_term()
        while self.current_token() and self.current_token()[1] in ["+", "-"]:
            op = self.consume("OPERADOR")[1]
            right = self.parse_term()
            left = {"type": "BinaryOp", "left": left, "op": op, "right": right}
        return left

    def parse_term(self):
        left = self.parse_factor()
        while self.current_token() and self.current_token()[1] in ["*", "/"]:
            op = self.consume("OPERADOR")[1]
            right = self.parse_factor()
            left = {"type": "BinaryOp", "left": left, "op": op, "right": right}
        return left

    def parse_factor(self):
        token = self.current_token()
        if token and token[0] == "IDENTIFICADOR":
            self.consume("IDENTIFICADOR")
            return {"type": "Identifier", "name": token[1]}
        elif token and token[0] == "NUMERO":
            self.consume("NUMERO")
            return {"type": "Number", "value": token[1]}
        elif token and token[0] == "STRING":
            self.consume("STRING")
            return {"type": "String", "value": token[1]}
        elif token and token[1] == "(":
            self.consume("SIMBOLO", "(")
            expr = self.parse_expression()
            self.consume("SIMBOLO", ")")
            return expr
        return None

def analizador_sintactico(tokens):
    parser = Parser(tokens)
    ast = parser.parse_program()
    return ast, parser.errors

# Análisis Semántico
class SemanticAnalyzer:
    def __init__(self):
        self.symbol_table = {}
        self.errors = []
        self.scope_stack = [{}]

    def enter_scope(self):
        self.scope_stack.append({})

    def exit_scope(self):
        self.scope_stack.pop()

    def declare_variable(self, name, var_type, line):
        current_scope = self.scope_stack[-1]
        if name in current_scope:
            self.errors.append(f"SEM-001: Error semántico: variable '{name}' ya declarada - línea {line}")
        else:
            current_scope[name] = {"type": var_type, "line": line}

    def lookup_variable(self, name):
        for scope in reversed(self.scope_stack):
            if name in scope:
                return scope[name]
        return None

    def analyze_program(self, ast):
        if ast and isinstance(ast, dict) and ast.get("class_decl"):
            self.analyze_class_declaration(ast["class_decl"])

    def analyze_class_declaration(self, class_decl):
        if not class_decl or not isinstance(class_decl, dict):
            return
        for decl in class_decl.get("declarations", []):
            if isinstance(decl, dict):
                if decl.get("type") == "VariableDeclaration":
                    self.declare_variable(decl["name"], decl["var_type"], 0)
                elif decl.get("type") == "MethodDeclaration":
                    self.enter_scope()
                    self.analyze_method_declaration(decl)
                    self.exit_scope()

    def analyze_method_declaration(self, method_decl):
        if not method_decl or not isinstance(method_decl, dict):
            return
        for stmt in method_decl.get("statements", []):
            self.analyze_statement(stmt)

    def analyze_statement(self, stmt):
        if not stmt or not isinstance(stmt, dict):
            return
        if stmt.get("type") == "VariableDeclaration":
            self.declare_variable(stmt["name"], stmt["var_type"], 0)
            if "init" in stmt:
                expr_type = self.analyze_expression(stmt["init"])
                if expr_type and expr_type != stmt["var_type"]:
                    self.errors.append(f"SEM-003: Error semántico: tipo incompatible en inicialización para '{stmt['name']}' - línea 1")
        elif stmt.get("type") == "Assignment":
            var_info = self.lookup_variable(stmt["name"])
            if not var_info:
                self.errors.append(f"SEM-002: Error semántico: variable '{stmt['name']}' no declarada - línea 1")
            else:
                expr_type = self.analyze_expression(stmt["expr"])
                if expr_type and expr_type != var_info["type"]:
                    self.errors.append(f"SEM-003: Error semántico: tipo incompatible en asignación para '{stmt['name']}' - línea 1")
        elif stmt.get("type") == "IfStatement":
            self.analyze_expression(stmt["condition"])
            self.enter_scope()
            for s in stmt.get("then_stmts", []):
                self.analyze_statement(s)
            self.exit_scope()
            if stmt.get("else_stmts"):
                self.enter_scope()
                for s in stmt["else_stmts"]:
                    self.analyze_statement(s)
                self.exit_scope()
        elif stmt.get("type") == "WhileStatement":
            self.analyze_expression(stmt["condition"])
            self.enter_scope()
            for s in stmt.get("stmts", []):
                self.analyze_statement(s)
            self.exit_scope()
        elif stmt.get("type") == "ReturnStatement":
            self.analyze_expression(stmt["expr"])

    def analyze_expression(self, expr):
        if not expr or not isinstance(expr, dict):
            return None
        if expr.get("type") == "Identifier":
            var_info = self.lookup_variable(expr["name"])
            if not var_info:
                self.errors.append(f"SEM-002: Error semántico: variable '{expr['name']}' no declarada")
                return None
            return var_info["type"]
        elif expr.get("type") == "Number":
            return "int"
        elif expr.get("type") == "String":
            return "String"
        elif expr.get("type") == "BinaryOp":
            left_type = self.analyze_expression(expr["left"])
            right_type = self.analyze_expression(expr["right"])
            op = expr["op"]
            if left_type == right_type == "int":
                if op in ["+", "-", "*", "/"]:
                    return "int"
                elif op in [">", "<", ">=", "<=", "==", "!="]:
                    return "boolean"
                else:
                    self.errors.append("SEM-005: Operador no soportado - línea 1")
                    return None
            else:
                self.errors.append("SEM-004: Error semántico: tipos incompatibles en operación - línea 1")
                return None
        return None

def analizador_semantico(ast, symbol_table):
    try:
        analyzer = SemanticAnalyzer()
        analyzer.symbol_table = symbol_table
        analyzer.analyze_program(ast)
        return analyzer.symbol_table, analyzer.errors
    except Exception as e:
        import traceback
        error_msg = f"Error en análisis semántico: {str(e)}\n{traceback.format_exc()}"
        return symbol_table, [error_msg]

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