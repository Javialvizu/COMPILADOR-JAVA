"""
COMPILADOR JAVA - Análisis Léxico, Sintáctico y Semántico
Versión corregida: errores semánticos estructurados, líneas/columnas reales y parser más seguro.
"""

KEYWORDS = {
    "class", "public", "static", "void", "int", "double", "String",
    "if", "else", "for", "while", "return", "new", "boolean", "char", "true", "false"
}

OPERADORES_DOBLES = {"==", "!=", "<=", ">=", "++", "--", "+=", "-=", "*=", "/="}
SIMBOLOS = "{}();,.[]"
TIPOS_JAVA = {"int", "double", "String", "boolean", "char"}


def es_letra(c):
    return c.isalpha() or c == "_"


def es_numero(c):
    return c.isdigit()


def crear_error(codigo, descripcion, linea="", columna=""):
    """Formato único para errores que JS puede dibujar como tabla."""
    return {
        "codigo": codigo,
        "descripcion": descripcion,
        "linea": linea,
        "columna": columna,
    }


# ==================== ANÁLISIS LÉXICO ====================
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

        # Comentario de una línea
        if codigo[i:i + 2] == "//":
            while i < len(codigo) and codigo[i] != "\n":
                i += 1
                columna += 1
            continue

        # Comentario multilínea
        if codigo[i:i + 2] == "/*":
            inicio_linea, inicio_columna = linea, columna
            i += 2
            columna += 2
            cerrado = False
            while i < len(codigo):
                if codigo[i:i + 2] == "*/":
                    i += 2
                    columna += 2
                    cerrado = True
                    break
                if codigo[i] == "\n":
                    linea += 1
                    columna = 1
                    i += 1
                else:
                    i += 1
                    columna += 1
            if not cerrado:
                errores.append(("ERROR", "Comentario multilínea sin cerrar", inicio_linea, inicio_columna))
            continue

        # Identificadores y palabras reservadas
        if es_letra(c):
            inicio = i
            col = columna
            while i < len(codigo) and (es_letra(codigo[i]) or es_numero(codigo[i])):
                i += 1
            lexema = codigo[inicio:i]
            tipo = "KEYWORD" if lexema in KEYWORDS else "IDENTIFICADOR"
            tokens.append((tipo, lexema, linea, col))

            if tipo == "IDENTIFICADOR" and lexema not in tabla_simbolos:
                tabla_simbolos[lexema] = {"tipo": "ID", "linea": linea}

            columna += len(lexema)
            continue

        # Números enteros y decimales
        if es_numero(c):
            inicio = i
            col = columna
            while i < len(codigo) and es_numero(codigo[i]):
                i += 1
            if i < len(codigo) and codigo[i] == ".":
                i += 1
                if i >= len(codigo) or not es_numero(codigo[i]):
                    errores.append(("ERROR", "Número decimal incompleto", linea, col))
                while i < len(codigo) and es_numero(codigo[i]):
                    i += 1
            lexema = codigo[inicio:i]
            tokens.append(("NUMERO", lexema, linea, col))
            columna += len(lexema)
            continue

        # Strings
        if c == '"':
            inicio = i
            col = columna
            inicio_linea = linea
            i += 1
            columna += 1
            cerrado = False
            while i < len(codigo):
                if codigo[i] == '"':
                    i += 1
                    columna += 1
                    cerrado = True
                    break
                if codigo[i] == "\n":
                    linea += 1
                    columna = 1
                    i += 1
                else:
                    i += 1
                    columna += 1
            lexema = codigo[inicio:i]
            if cerrado:
                tokens.append(("STRING", lexema, inicio_linea, col))
            else:
                errores.append(("ERROR", "Cadena sin cerrar", inicio_linea, col))
            continue

        if codigo[i:i + 2] in OPERADORES_DOBLES:
            tokens.append(("OPERADOR", codigo[i:i + 2], linea, columna))
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


# ==================== PARSER ====================
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.errors = []

    def current_token(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def token_line(self, token):
        return token[2] if token and len(token) > 2 else ""

    def token_col(self, token):
        return token[3] if token and len(token) > 3 else ""

    def consume(self, expected_type=None, expected_value=None):
        token = self.current_token()
        if token is None:
            self.errors.append(crear_error("SYN-002", "Token inesperado al final", "", ""))
            return None

        tipo_ok = expected_type is None or token[0] == expected_type
        valor_ok = expected_value is None or token[1] == expected_value
        if not (tipo_ok and valor_ok):
            esperado = " ".join(x for x in [expected_type, expected_value] if x)
            encontrado = f"{token[0]} {token[1]}"
            self.errors.append(crear_error(
                "SYN-001",
                f"Se esperaba {esperado}, encontrado {encontrado}",
                token[2],
                token[3],
            ))
            self.pos += 1
            return None

        self.pos += 1
        return token

    def synchronize(self):
        while self.current_token() and self.current_token()[1] not in [";", "}"]:
            self.pos += 1
        if self.current_token() and self.current_token()[1] == ";":
            self.pos += 1

    def parse_program(self):
        class_decl = self.parse_class_declaration()
        return {"type": "Program", "class_decl": class_decl} if class_decl else None

    def parse_class_declaration(self):
        self.consume("KEYWORD", "class")
        name_token = self.consume("IDENTIFICADOR")
        if not name_token:
            return None
        self.consume("SIMBOLO", "{")

        declarations = []
        while self.current_token() and self.current_token()[1] != "}":
            pos_antes = self.pos
            decl = self.parse_declaration()
            if decl:
                declarations.append(decl)
            if self.pos == pos_antes:
                tok = self.current_token()
                self.errors.append(crear_error("SYN-003", f"Declaración no reconocida: {tok[1]}", tok[2], tok[3]))
                self.pos += 1

        self.consume("SIMBOLO", "}")
        return {
            "type": "ClassDeclaration",
            "name": name_token[1],
            "line": name_token[2],
            "column": name_token[3],
            "declarations": declarations,
        }

    def parse_declaration(self):
        token = self.current_token()
        if token and token[0] == "KEYWORD" and token[1] in TIPOS_JAVA:
            var_type = self.consume("KEYWORD")
            name_token = self.consume("IDENTIFICADOR")
            self.consume("SIMBOLO", ";")
            if not name_token:
                return None
            return {
                "type": "VariableDeclaration",
                "var_type": var_type[1],
                "name": name_token[1],
                "line": name_token[2],
                "column": name_token[3],
            }
        if token and token[1] == "public":
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
        while self.current_token() and self.current_token()[1] != "}":
            pos_antes = self.pos
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
            if self.pos == pos_antes:
                tok = self.current_token()
                self.errors.append(crear_error("SYN-004", f"Sentencia no reconocida: {tok[1]}", tok[2], tok[3]))
                self.synchronize()

        self.consume("SIMBOLO", "}")
        return {
            "type": "MethodDeclaration",
            "name": name_token[1] if name_token else "",
            "line": self.token_line(name_token),
            "column": self.token_col(name_token),
            "statements": statements,
        }

    def parse_statement(self):
        token = self.current_token()
        if not token:
            return None

        if token[0] == "KEYWORD" and token[1] in TIPOS_JAVA:
            var_type = self.consume("KEYWORD")
            name_token = self.consume("IDENTIFICADOR")
            self.consume("OPERADOR", "=")
            expr = self.parse_expression()
            self.consume("SIMBOLO", ";")
            if not name_token:
                return None
            return {
                "type": "VariableDeclaration",
                "var_type": var_type[1],
                "name": name_token[1],
                "line": name_token[2],
                "column": name_token[3],
                "init": expr,
            }

        if token[0] == "IDENTIFICADOR":
            name_token = self.consume("IDENTIFICADOR")
            self.consume("OPERADOR", "=")
            expr = self.parse_expression()
            self.consume("SIMBOLO", ";")
            return {
                "type": "Assignment",
                "name": name_token[1],
                "line": name_token[2],
                "column": name_token[3],
                "expr": expr,
            }

        if token[1] == "if":
            return self.parse_if_statement()
        if token[1] == "while":
            return self.parse_while_statement()
        if token[1] == "return":
            return_token = self.consume("KEYWORD", "return")
            expr = self.parse_expression()
            self.consume("SIMBOLO", ";")
            return {
                "type": "ReturnStatement",
                "line": return_token[2] if return_token else "",
                "column": return_token[3] if return_token else "",
                "expr": expr,
            }
        return None

    def parse_block_statements(self):
        statements = []
        self.consume("SIMBOLO", "{")
        while self.current_token() and self.current_token()[1] != "}":
            pos_antes = self.pos
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
            if self.pos == pos_antes:
                tok = self.current_token()
                self.errors.append(crear_error("SYN-004", f"Sentencia no reconocida: {tok[1]}", tok[2], tok[3]))
                self.synchronize()
        self.consume("SIMBOLO", "}")
        return statements

    def parse_if_statement(self):
        if_token = self.consume("KEYWORD", "if")
        self.consume("SIMBOLO", "(")
        condition = self.parse_expression()
        self.consume("SIMBOLO", ")")
        then_stmts = self.parse_block_statements()
        else_stmts = []
        if self.current_token() and self.current_token()[1] == "else":
            self.consume("KEYWORD", "else")
            else_stmts = self.parse_block_statements()
        return {
            "type": "IfStatement",
            "line": self.token_line(if_token),
            "column": self.token_col(if_token),
            "condition": condition,
            "then_stmts": then_stmts,
            "else_stmts": else_stmts,
        }

    def parse_while_statement(self):
        while_token = self.consume("KEYWORD", "while")
        self.consume("SIMBOLO", "(")
        condition = self.parse_expression()
        self.consume("SIMBOLO", ")")
        stmts = self.parse_block_statements()
        return {
            "type": "WhileStatement",
            "line": self.token_line(while_token),
            "column": self.token_col(while_token),
            "condition": condition,
            "stmts": stmts,
        }

    def parse_expression(self):
        return self.parse_comparison()

    def parse_comparison(self):
        left = self.parse_additive()
        while self.current_token() and self.current_token()[1] in [">", "<", ">=", "<=", "==", "!="]:
            op_token = self.consume("OPERADOR")
            right = self.parse_additive()
            left = {"type": "BinaryOp", "left": left, "op": op_token[1], "line": op_token[2], "column": op_token[3], "right": right}
        return left

    def parse_additive(self):
        left = self.parse_term()
        while self.current_token() and self.current_token()[1] in ["+", "-"]:
            op_token = self.consume("OPERADOR")
            right = self.parse_term()
            left = {"type": "BinaryOp", "left": left, "op": op_token[1], "line": op_token[2], "column": op_token[3], "right": right}
        return left

    def parse_term(self):
        left = self.parse_factor()
        while self.current_token() and self.current_token()[1] in ["*", "/"]:
            op_token = self.consume("OPERADOR")
            right = self.parse_factor()
            left = {"type": "BinaryOp", "left": left, "op": op_token[1], "line": op_token[2], "column": op_token[3], "right": right}
        return left

    def parse_factor(self):
        token = self.current_token()
        if not token:
            self.errors.append(crear_error("SYN-005", "Expresión incompleta", "", ""))
            return None

        if token[0] == "IDENTIFICADOR":
            self.consume("IDENTIFICADOR")
            return {"type": "Identifier", "name": token[1], "line": token[2], "column": token[3]}
        if token[0] == "NUMERO":
            self.consume("NUMERO")
            return {"type": "Number", "value": token[1], "line": token[2], "column": token[3]}
        if token[0] == "STRING":
            self.consume("STRING")
            return {"type": "String", "value": token[1], "line": token[2], "column": token[3]}
        if token[0] == "KEYWORD" and token[1] in ["true", "false"]:
            self.consume("KEYWORD")
            return {"type": "Boolean", "value": token[1], "line": token[2], "column": token[3]}
        if token[1] == "(":
            self.consume("SIMBOLO", "(")
            expr = self.parse_expression()
            self.consume("SIMBOLO", ")")
            return expr

        self.errors.append(crear_error("SYN-005", f"Factor inválido: {token[1]}", token[2], token[3]))
        self.pos += 1
        return None


def analizador_sintactico(tokens):
    parser = Parser(tokens)
    ast = parser.parse_program()
    return ast, parser.errors


# ==================== ANÁLISIS SEMÁNTICO ====================
class SemanticAnalyzer:
    def __init__(self, symbol_table=None):
        self.symbol_table = symbol_table if isinstance(symbol_table, dict) else {}
        self.errors = []
        self.scope_stack = [{}]

    def enter_scope(self):
        self.scope_stack.append({})

    def exit_scope(self):
        if len(self.scope_stack) > 1:
            self.scope_stack.pop()

    def add_error(self, codigo, descripcion, node=None):
        self.errors.append(crear_error(
            codigo,
            descripcion,
            node.get("line", "") if isinstance(node, dict) else "",
            node.get("column", "") if isinstance(node, dict) else "",
        ))

    def declare_variable(self, name, var_type, node):
        current_scope = self.scope_stack[-1]
        if name in current_scope:
            self.add_error("SEM-001", f"Variable '{name}' ya declarada en este alcance", node)
            return
        current_scope[name] = {"type": var_type, "line": node.get("line", ""), "column": node.get("column", "")}
        self.symbol_table[name] = {"tipo": var_type, "linea": node.get("line", "")}

    def lookup_variable(self, name):
        for scope in reversed(self.scope_stack):
            if name in scope:
                return scope[name]
        return None

    def analyze_program(self, ast):
        if isinstance(ast, dict) and ast.get("class_decl"):
            self.analyze_class_declaration(ast["class_decl"])

    def analyze_class_declaration(self, class_decl):
        for decl in class_decl.get("declarations", []):
            if not isinstance(decl, dict):
                continue
            if decl.get("type") == "VariableDeclaration":
                self.declare_variable(decl["name"], decl["var_type"], decl)
            elif decl.get("type") == "MethodDeclaration":
                self.enter_scope()
                self.analyze_method_declaration(decl)
                self.exit_scope()

    def analyze_method_declaration(self, method_decl):
        for stmt in method_decl.get("statements", []):
            self.analyze_statement(stmt)

    def analyze_statement(self, stmt):
        if not isinstance(stmt, dict):
            return

        tipo_stmt = stmt.get("type")
        if tipo_stmt == "VariableDeclaration":
            self.declare_variable(stmt["name"], stmt["var_type"], stmt)
            if "init" in stmt:
                expr_type = self.analyze_expression(stmt["init"])
                if expr_type and not self.types_compatible(stmt["var_type"], expr_type):
                    self.add_error("SEM-003", f"Tipo incompatible en inicialización de '{stmt['name']}': se esperaba {stmt['var_type']} y se recibió {expr_type}", stmt)

        elif tipo_stmt == "Assignment":
            var_info = self.lookup_variable(stmt["name"])
            if not var_info:
                self.add_error("SEM-002", f"Variable '{stmt['name']}' no declarada", stmt)
            else:
                expr_type = self.analyze_expression(stmt.get("expr"))
                if expr_type and not self.types_compatible(var_info["type"], expr_type):
                    self.add_error("SEM-003", f"Tipo incompatible en asignación de '{stmt['name']}': se esperaba {var_info['type']} y se recibió {expr_type}", stmt)

        elif tipo_stmt == "IfStatement":
            condition_type = self.analyze_expression(stmt.get("condition"))
            if condition_type and condition_type != "boolean":
                self.add_error("SEM-006", "La condición del if debe ser booleana", stmt)
            self.enter_scope()
            for s in stmt.get("then_stmts", []):
                self.analyze_statement(s)
            self.exit_scope()
            self.enter_scope()
            for s in stmt.get("else_stmts", []):
                self.analyze_statement(s)
            self.exit_scope()

        elif tipo_stmt == "WhileStatement":
            condition_type = self.analyze_expression(stmt.get("condition"))
            if condition_type and condition_type != "boolean":
                self.add_error("SEM-006", "La condición del while debe ser booleana", stmt)
            self.enter_scope()
            for s in stmt.get("stmts", []):
                self.analyze_statement(s)
            self.exit_scope()

        elif tipo_stmt == "ReturnStatement":
            self.analyze_expression(stmt.get("expr"))

    def analyze_expression(self, expr):
        if not isinstance(expr, dict):
            return None

        tipo_expr = expr.get("type")
        if tipo_expr == "Identifier":
            var_info = self.lookup_variable(expr["name"])
            if not var_info:
                self.add_error("SEM-002", f"Variable '{expr['name']}' no declarada", expr)
                return None
            return var_info["type"]

        if tipo_expr == "Number":
            return "double" if "." in str(expr.get("value", "")) else "int"
        if tipo_expr == "String":
            return "String"
        if tipo_expr == "Boolean":
            return "boolean"

        if tipo_expr == "BinaryOp":
            left_type = self.analyze_expression(expr.get("left"))
            right_type = self.analyze_expression(expr.get("right"))
            op = expr.get("op")
            if not left_type or not right_type:
                return None

            if op in ["+", "-", "*", "/"]:
                if left_type in ["int", "double"] and right_type in ["int", "double"]:
                    return "double" if "double" in [left_type, right_type] else "int"
                if op == "+" and (left_type == "String" or right_type == "String"):
                    return "String"
                self.add_error("SEM-004", f"Tipos incompatibles en operación '{op}': {left_type} con {right_type}", expr)
                return None

            if op in [">", "<", ">=", "<="]:
                if left_type in ["int", "double"] and right_type in ["int", "double"]:
                    return "boolean"
                self.add_error("SEM-004", f"Comparación inválida entre {left_type} y {right_type}", expr)
                return None

            if op in ["==", "!="]:
                if self.types_compatible(left_type, right_type) or self.types_compatible(right_type, left_type):
                    return "boolean"
                self.add_error("SEM-004", f"Comparación inválida entre {left_type} y {right_type}", expr)
                return None

            self.add_error("SEM-005", f"Operador no soportado: {op}", expr)
            return None

        return None

    def types_compatible(self, expected, received):
        if expected == received:
            return True
        # Java permite asignar int a double sin pérdida crítica en este analizador básico.
        if expected == "double" and received == "int":
            return True
        return False


def analizador_semantico(ast, symbol_table):
    try:
        analyzer = SemanticAnalyzer(symbol_table)
        analyzer.analyze_program(ast)
        return analyzer.symbol_table, analyzer.errors
    except Exception as e:
        return symbol_table, [crear_error("SEM-999", f"Error interno en análisis semántico: {str(e)}", "", "")]
