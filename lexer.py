KEYWORDS = {
    "class", "public", "static", "void", "int", "double", "String",
    "if", "else", "for", "while", "return", "new", "boolean", "char",
    "import", "true", "false"
}

OPERADORES_DOBLES = {"==", "!=", "<=", ">=", "++", "--", "+=", "-=", "*=", "/="}
SIMBOLOS = "{}();,.[]"


def es_letra(c):
    return c.isalpha() or c == "_"


def es_numero(c):
    return c.isdigit()


# ==================== PARSER ====================

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
                self.errors.append({
                    "description": f"Error sintáctico: esperado {expected_type or ''} {expected_value or ''}, encontrado {token[0]} {token[1]}",
                    "line": token[2],
                    "column": token[3]
                })
                self.pos += 1
                return None

            self.pos += 1
            return token

        self.errors.append({
            "description": "Error sintáctico: token inesperado al final",
            "line": "",
            "column": ""
        })
        return None

    def parse_program(self):
        imports = []

        while self.current_token() and self.current_token()[0] == "KEYWORD" and self.current_token()[1] == "import":
            imp = self.parse_import_declaration()
            if imp:
                imports.append(imp)

        class_decl = self.parse_class_declaration()

        if not class_decl:
            return None

        return {
            "type": "Program",
            "imports": imports,
            "class_decl": class_decl
        }

    def parse_import_declaration(self):
        self.consume("KEYWORD", "import")
        path = self.parse_qualified_name()
        self.consume("SIMBOLO", ";")

        return {
            "type": "ImportDeclaration",
            "path": path
        }

    def parse_qualified_name(self):
        name_token = self.consume("IDENTIFICADOR")

        if not name_token:
            return None

        name = name_token[1]

        while self.current_token() and self.current_token()[1] == ".":
            self.consume("SIMBOLO", ".")
            part_token = self.consume("IDENTIFICADOR")

            if not part_token:
                break

            name += "." + part_token[1]

        return name

    def parse_class_declaration(self):
        token = self.current_token()

        if token and token[0] == "KEYWORD" and token[1] == "public":
            self.consume("KEYWORD", "public")

        self.consume("KEYWORD", "class")
        name_token = self.consume("IDENTIFICADOR")

        if not name_token:
            return None

        self.consume("SIMBOLO", "{")

        declarations = []
        max_iter = 1000
        iter_count = 0

        while self.current_token() and self.current_token()[1] != "}" and iter_count < max_iter:
            start_pos = self.pos
            decl = self.parse_declaration()

            if decl:
                declarations.append(decl)
            elif self.pos == start_pos:
                token = self.current_token()
                self.errors.append({
                    "description": f"Error sintáctico: declaración no válida cerca de '{token[1]}'",
                    "line": token[2],
                    "column": token[3]
                })
                self.pos += 1

            iter_count += 1

        if iter_count >= max_iter:
            self.errors.append({
                "description": "Posible bucle infinito en declaraciones de clase",
                "line": "",
                "column": ""
            })

        self.consume("SIMBOLO", "}")

        return {
            "type": "ClassDeclaration",
            "name": name_token[1],
            "declarations": declarations,
            "line": name_token[2],
            "column": name_token[3]
        }

    def parse_type(self):
        token = self.current_token()

        if token and token[0] == "KEYWORD" and token[1] in ["int", "double", "String", "boolean", "char"]:
            type_name = self.consume("KEYWORD", token[1])[1]

            if self.current_token() and self.current_token()[1] == "[":
                self.consume("SIMBOLO", "[")
                self.consume("SIMBOLO", "]")
                type_name += "[]"

            return type_name

        # Tipos personalizados como MiClase obj;
        if token and token[0] == "IDENTIFICADOR":
            type_name = self.consume("IDENTIFICADOR")[1]

            if self.current_token() and self.current_token()[1] == "[":
                self.consume("SIMBOLO", "[")
                self.consume("SIMBOLO", "]")
                type_name += "[]"

            return type_name

        return None

    def parse_parameter_list(self):
        params = []

        if self.current_token() and self.current_token()[1] != ")":
            while True:
                param_type = self.parse_type()
                param_name_token = self.consume("IDENTIFICADOR")

                if param_type and param_name_token:
                    params.append({
                        "name": param_name_token[1],
                        "type": param_type,
                        "line": param_name_token[2],
                        "column": param_name_token[3]
                    })

                if self.current_token() and self.current_token()[1] == ",":
                    self.consume("SIMBOLO", ",")
                    continue

                break

        return params

    def parse_declaration(self):
        token = self.current_token()

        if token and token[0] == "KEYWORD" and token[1] == "public":
            return self.parse_method_declaration()

        start_pos = self.pos
        var_type = self.parse_type()

        if var_type and self.current_token() and self.current_token()[0] == "IDENTIFICADOR":
            name_token = self.consume("IDENTIFICADOR")

            init = None
            if self.current_token() and self.current_token()[1] == "=":
                self.consume("OPERADOR", "=")
                init = self.parse_expression()

            self.consume("SIMBOLO", ";")

            node = {
                "type": "VariableDeclaration",
                "var_type": var_type,
                "name": name_token[1],
                "line": name_token[2],
                "column": name_token[3]
            }

            if init is not None:
                node["init"] = init

            return node

        self.pos = start_pos
        return None

    def parse_method_declaration(self):
        self.consume("KEYWORD", "public")
        self.consume("KEYWORD", "static")
        self.consume("KEYWORD", "void")

        name_token = self.consume("IDENTIFICADOR")

        self.consume("SIMBOLO", "(")
        params = self.parse_parameter_list()
        self.consume("SIMBOLO", ")")
        self.consume("SIMBOLO", "{")

        statements = []
        max_iter = 1000
        iter_count = 0

        while self.current_token() and self.current_token()[1] != "}" and iter_count < max_iter:
            start_pos = self.pos
            stmt = self.parse_statement()

            if stmt:
                statements.append(stmt)
            elif self.pos == start_pos:
                token = self.current_token()
                self.errors.append({
                    "description": f"Error sintáctico: sentencia no válida cerca de '{token[1]}'",
                    "line": token[2],
                    "column": token[3]
                })
                self.pos += 1

            iter_count += 1

        if iter_count >= max_iter:
            self.errors.append({
                "description": "Posible bucle infinito en statements del método",
                "line": "",
                "column": ""
            })

        self.consume("SIMBOLO", "}")

        return {
            "type": "MethodDeclaration",
            "name": name_token[1] if name_token else "main",
            "params": params,
            "statements": statements,
            "line": name_token[2] if name_token else "",
            "column": name_token[3] if name_token else ""
        }

    def parse_statement(self):
        start_pos = self.pos
        var_type = self.parse_type()

        if var_type:
            if self.current_token() and self.current_token()[0] == "IDENTIFICADOR":
                name_token = self.consume("IDENTIFICADOR")
                init = None

                if self.current_token() and self.current_token()[1] == "=":
                    self.consume("OPERADOR", "=")
                    init = self.parse_expression()

                self.consume("SIMBOLO", ";")

                node = {
                    "type": "VariableDeclaration",
                    "var_type": var_type,
                    "name": name_token[1],
                    "line": name_token[2],
                    "column": name_token[3]
                }

                if init is not None:
                    node["init"] = init

                return node

            self.pos = start_pos

        token = self.current_token()

        if token and token[0] == "IDENTIFICADOR":
            name_token = self.consume("IDENTIFICADOR")

            if self.current_token() and self.current_token()[1] == "=":
                self.consume("OPERADOR", "=")
                right = self.parse_expression()
                self.consume("SIMBOLO", ";")

                return {
                    "type": "Assignment",
                    "name": name_token[1],
                    "expr": right,
                    "line": name_token[2],
                    "column": name_token[3]
                }

            # Si no era asignación, lo tratamos como expresión simple
            self.pos = start_pos
            expr = self.parse_expression()
            self.consume("SIMBOLO", ";")

            return {
                "type": "ExpressionStatement",
                "expr": expr,
                "line": token[2],
                "column": token[3]
            }

        if token and token[0] == "KEYWORD" and token[1] == "if":
            return self.parse_if_statement()

        if token and token[0] == "KEYWORD" and token[1] == "while":
            return self.parse_while_statement()

        if token and token[0] == "KEYWORD" and token[1] == "return":
            return self.parse_return_statement()

        return None

    def parse_return_statement(self):
        return_token = self.consume("KEYWORD", "return")
        expr = self.parse_expression()
        self.consume("SIMBOLO", ";")

        return {
            "type": "ReturnStatement",
            "expr": expr,
            "line": return_token[2] if return_token else "",
            "column": return_token[3] if return_token else ""
        }

    def parse_if_statement(self):
        if_token = self.consume("KEYWORD", "if")

        self.consume("SIMBOLO", "(")
        condition = self.parse_expression()
        self.consume("SIMBOLO", ")")
        self.consume("SIMBOLO", "{")

        then_stmts = []

        while self.current_token() and self.current_token()[1] != "}":
            stmt = self.parse_statement()
            if stmt:
                then_stmts.append(stmt)
            else:
                self.pos += 1

        self.consume("SIMBOLO", "}")

        else_stmts = []

        if self.current_token() and self.current_token()[0] == "KEYWORD" and self.current_token()[1] == "else":
            self.consume("KEYWORD", "else")
            self.consume("SIMBOLO", "{")

            while self.current_token() and self.current_token()[1] != "}":
                stmt = self.parse_statement()
                if stmt:
                    else_stmts.append(stmt)
                else:
                    self.pos += 1

            self.consume("SIMBOLO", "}")

        return {
            "type": "IfStatement",
            "condition": condition,
            "then_stmts": then_stmts,
            "else_stmts": else_stmts,
            "line": if_token[2] if if_token else "",
            "column": if_token[3] if if_token else ""
        }

    def parse_while_statement(self):
        while_token = self.consume("KEYWORD", "while")

        self.consume("SIMBOLO", "(")
        condition = self.parse_expression()
        self.consume("SIMBOLO", ")")
        self.consume("SIMBOLO", "{")

        stmts = []

        while self.current_token() and self.current_token()[1] != "}":
            stmt = self.parse_statement()
            if stmt:
                stmts.append(stmt)
            else:
                self.pos += 1

        self.consume("SIMBOLO", "}")

        return {
            "type": "WhileStatement",
            "condition": condition,
            "stmts": stmts,
            "line": while_token[2] if while_token else "",
            "column": while_token[3] if while_token else ""
        }

    def parse_expression(self):
        return self.parse_comparison()

    def parse_comparison(self):
        left = self.parse_additive()

        while self.current_token() and self.current_token()[1] in [">", "<", ">=", "<=", "==", "!="]:
            op_token = self.consume("OPERADOR")
            right = self.parse_additive()

            left = {
                "type": "BinaryOp",
                "left": left,
                "op": op_token[1] if op_token else "",
                "right": right,
                "line": op_token[2] if op_token else "",
                "column": op_token[3] if op_token else ""
            }

        return left

    def parse_additive(self):
        left = self.parse_term()

        while self.current_token() and self.current_token()[1] in ["+", "-"]:
            op_token = self.consume("OPERADOR")
            right = self.parse_term()

            left = {
                "type": "BinaryOp",
                "left": left,
                "op": op_token[1] if op_token else "",
                "right": right,
                "line": op_token[2] if op_token else "",
                "column": op_token[3] if op_token else ""
            }

        return left

    def parse_term(self):
        left = self.parse_factor()

        while self.current_token() and self.current_token()[1] in ["*", "/"]:
            op_token = self.consume("OPERADOR")
            right = self.parse_factor()

            left = {
                "type": "BinaryOp",
                "left": left,
                "op": op_token[1] if op_token else "",
                "right": right,
                "line": op_token[2] if op_token else "",
                "column": op_token[3] if op_token else ""
            }

        return left

    def parse_factor(self):
        token = self.current_token()

        if not token:
            return None

        node = None

        if token[0] == "KEYWORD" and token[1] == "new":
            self.consume("KEYWORD", "new")
            class_token = self.consume("IDENTIFICADOR")
            self.consume("SIMBOLO", "(")

            args = []

            if self.current_token() and self.current_token()[1] != ")":
                args.append(self.parse_expression())

                while self.current_token() and self.current_token()[1] == ",":
                    self.consume("SIMBOLO", ",")
                    args.append(self.parse_expression())

            self.consume("SIMBOLO", ")")

            node = {
                "type": "NewExpression",
                "class": class_token[1] if class_token else "",
                "args": args,
                "line": class_token[2] if class_token else "",
                "column": class_token[3] if class_token else ""
            }

        elif token[0] == "KEYWORD" and token[1] in ["true", "false"]:
            self.consume("KEYWORD", token[1])

            node = {
                "type": "Boolean",
                "value": token[1],
                "line": token[2],
                "column": token[3]
            }

        elif token[0] == "IDENTIFICADOR":
            self.consume("IDENTIFICADOR")

            node = {
                "type": "Identifier",
                "name": token[1],
                "line": token[2],
                "column": token[3]
            }

            if self.current_token() and self.current_token()[1] == "(":
                self.consume("SIMBOLO", "(")
                args = []

                if self.current_token() and self.current_token()[1] != ")":
                    args.append(self.parse_expression())

                    while self.current_token() and self.current_token()[1] == ",":
                        self.consume("SIMBOLO", ",")
                        args.append(self.parse_expression())

                self.consume("SIMBOLO", ")")

                node = {
                    "type": "MethodCall",
                    "receiver": None,
                    "method": token[1],
                    "args": args,
                    "line": token[2],
                    "column": token[3]
                }

        elif token[0] == "NUMERO":
            self.consume("NUMERO")

            node = {
                "type": "Number",
                "value": token[1],
                "line": token[2],
                "column": token[3]
            }

        elif token[0] == "STRING":
            self.consume("STRING")

            node = {
                "type": "String",
                "value": token[1],
                "line": token[2],
                "column": token[3]
            }

        elif token[1] == "(":
            self.consume("SIMBOLO", "(")
            node = self.parse_expression()
            self.consume("SIMBOLO", ")")

        else:
            self.errors.append({
                "description": f"Error sintáctico: factor inesperado '{token[1]}'",
                "line": token[2],
                "column": token[3]
            })
            self.pos += 1
            return None

        while self.current_token() and self.current_token()[1] == ".":
            self.consume("SIMBOLO", ".")
            member_token = self.consume("IDENTIFICADOR")

            if not member_token:
                break

            if self.current_token() and self.current_token()[1] == "(":
                self.consume("SIMBOLO", "(")
                args = []

                if self.current_token() and self.current_token()[1] != ")":
                    args.append(self.parse_expression())

                    while self.current_token() and self.current_token()[1] == ",":
                        self.consume("SIMBOLO", ",")
                        args.append(self.parse_expression())

                self.consume("SIMBOLO", ")")

                node = {
                    "type": "MethodCall",
                    "receiver": node,
                    "method": member_token[1],
                    "args": args,
                    "line": member_token[2],
                    "column": member_token[3]
                }

            else:
                node = {
                    "type": "FieldAccess",
                    "receiver": node,
                    "field": member_token[1],
                    "line": member_token[2],
                    "column": member_token[3]
                }

        return node


def analizador_sintactico(tokens):
    parser = Parser(tokens)
    ast = parser.parse_program()
    return ast, parser.errors


# ==================== ANALIZADOR SEMÁNTICO ====================

class SemanticAnalyzer:
    def __init__(self):
        self.symbol_table = {}
        self.errors = []
        self.scope_stack = [{}]

    def enter_scope(self):
        self.scope_stack.append({})

    def exit_scope(self):
        if len(self.scope_stack) > 1:
            self.scope_stack.pop()

    def format_error(self, code, message, line=None, column=None):
        return {
            "code": code,
            "description": message,
            "line": line if line is not None else "",
            "column": column if column is not None else ""
        }

    def add_symbol_to_display_table(self, name, var_type, line, column=None, scope="local"):
        self.symbol_table[name] = {
            "tipo": var_type,
            "linea": line,
            "columna": column if column is not None else "",
            "ambito": scope
        }

    def declare_variable(self, name, var_type, line, column=None, scope="local"):
        current_scope = self.scope_stack[-1]

        if name in current_scope:
            self.errors.append(
                self.format_error(
                    "SEM-001",
                    f"Variable '{name}' ya declarada en este ámbito",
                    line,
                    column
                )
            )
            return False

        current_scope[name] = {
            "type": var_type,
            "line": line,
            "column": column,
            "scope": scope
        }

        self.add_symbol_to_display_table(name, var_type, line, column, scope)
        return True

    def lookup_variable(self, name):
        for scope in reversed(self.scope_stack):
            if name in scope:
                return scope[name]
        return None

    def analyze_program(self, ast):
        if ast and isinstance(ast, dict):
            self.analyze_class_declaration(ast.get("class_decl"))

    def analyze_class_declaration(self, class_decl):
        if not class_decl or not isinstance(class_decl, dict):
            return

        self.enter_scope()

        for decl in class_decl.get("declarations", []):
            if not isinstance(decl, dict):
                continue

            if decl.get("type") == "VariableDeclaration":
                self.analyze_variable_declaration(decl, scope="class")
            elif decl.get("type") == "MethodDeclaration":
                self.analyze_method_declaration(decl)

        self.exit_scope()

    def analyze_method_declaration(self, method_decl):
        if not method_decl or not isinstance(method_decl, dict):
            return

        self.enter_scope()

        for param in method_decl.get("params", []):
            self.declare_variable(
                param.get("name"),
                param.get("type"),
                param.get("line", ""),
                param.get("column", ""),
                scope="param"
            )

        for stmt in method_decl.get("statements", []):
            self.analyze_statement(stmt)

        self.exit_scope()

    def analyze_variable_declaration(self, stmt, scope="local"):
        name = stmt.get("name")
        var_type = stmt.get("var_type")
        line = stmt.get("line", "")
        column = stmt.get("column", "")

        self.declare_variable(name, var_type, line, column, scope)

        if "init" in stmt:
            expr_type = self.analyze_expression(stmt.get("init"))

            if expr_type and not self.is_assignable(var_type, expr_type):
                self.errors.append(
                    self.format_error(
                        "SEM-003",
                        f"Tipo incompatible en inicialización de '{name}': se esperaba '{var_type}' pero se obtuvo '{expr_type}'",
                        line,
                        column
                    )
                )

    def analyze_statement(self, stmt):
        if not stmt or not isinstance(stmt, dict):
            return

        stmt_type = stmt.get("type")
        line = stmt.get("line", "")
        column = stmt.get("column", "")

        if stmt_type == "VariableDeclaration":
            self.analyze_variable_declaration(stmt, scope="local")

        elif stmt_type == "Assignment":
            name = stmt.get("name")
            var_info = self.lookup_variable(name)

            if not var_info:
                self.errors.append(
                    self.format_error(
                        "SEM-002",
                        f"Variable '{name}' no declarada",
                        line,
                        column
                    )
                )
                self.analyze_expression(stmt.get("expr"))
                return

            expr_type = self.analyze_expression(stmt.get("expr"))

            if expr_type and not self.is_assignable(var_info.get("type"), expr_type):
                self.errors.append(
                    self.format_error(
                        "SEM-003",
                        f"Tipo incompatible en asignación de '{name}': se esperaba '{var_info.get('type')}' pero se obtuvo '{expr_type}'",
                        line,
                        column
                    )
                )

        elif stmt_type == "ExpressionStatement":
            self.analyze_expression(stmt.get("expr"))

        elif stmt_type == "IfStatement":
            condition_type = self.analyze_expression(stmt.get("condition"))

            if condition_type and condition_type != "boolean":
                self.errors.append(
                    self.format_error(
                        "SEM-006",
                        f"La condición del if debe ser boolean, pero se obtuvo '{condition_type}'",
                        line,
                        column
                    )
                )

            self.enter_scope()
            for s in stmt.get("then_stmts", []):
                self.analyze_statement(s)
            self.exit_scope()

            self.enter_scope()
            for s in stmt.get("else_stmts", []):
                self.analyze_statement(s)
            self.exit_scope()

        elif stmt_type == "WhileStatement":
            condition_type = self.analyze_expression(stmt.get("condition"))

            if condition_type and condition_type != "boolean":
                self.errors.append(
                    self.format_error(
                        "SEM-006",
                        f"La condición del while debe ser boolean, pero se obtuvo '{condition_type}'",
                        line,
                        column
                    )
                )

            self.enter_scope()
            for s in stmt.get("stmts", []):
                self.analyze_statement(s)
            self.exit_scope()

        elif stmt_type == "ReturnStatement":
            self.analyze_expression(stmt.get("expr"))

    def is_assignable(self, expected_type, received_type):
        if expected_type == received_type:
            return True

        # Permitir asignar int a double: double precio = 10;
        if expected_type == "double" and received_type == "int":
            return True

        return False

    def analyze_expression(self, expr):
        if not expr or not isinstance(expr, dict):
            return None

        expr_type = expr.get("type")

        if expr_type == "Identifier":
            name = expr.get("name")
            var_info = self.lookup_variable(name)

            if not var_info:
                if name in ["System", "Math", "Random"]:
                    return name

                self.errors.append(
                    self.format_error(
                        "SEM-002",
                        f"Variable '{name}' no declarada",
                        expr.get("line", ""),
                        expr.get("column", "")
                    )
                )
                return None

            return var_info.get("type")

        if expr_type == "Number":
            value = str(expr.get("value", ""))
            return "double" if "." in value else "int"

        if expr_type == "String":
            return "String"

        if expr_type == "Boolean":
            return "boolean"

        if expr_type == "FieldAccess":
            receiver_type = self.analyze_expression(expr.get("receiver"))

            if receiver_type == "System" and expr.get("field") == "out":
                return "PrintStream"

            return None

        if expr_type == "NewExpression":
            return expr.get("class")

        if expr_type == "MethodCall":
            receiver = expr.get("receiver")
            method = expr.get("method")
            args = expr.get("args", [])

            if receiver:
                receiver_type = self.analyze_expression(receiver)

                if receiver_type == "Random" and method == "nextInt":
                    if len(args) == 1 and self.analyze_expression(args[0]) == "int":
                        return "int"

                    self.errors.append(
                        self.format_error(
                            "SEM-005",
                            f"Argumentos inválidos para {method}",
                            expr.get("line", ""),
                            expr.get("column", "")
                        )
                    )
                    return None

                if receiver_type == "PrintStream" and method == "println":
                    for arg in args:
                        self.analyze_expression(arg)
                    return "void"

            return None

        if expr_type == "BinaryOp":
            left_type = self.analyze_expression(expr.get("left"))
            right_type = self.analyze_expression(expr.get("right"))
            op = expr.get("op")

            if not left_type or not right_type:
                return None

            if op == "+" and (left_type == "String" or right_type == "String"):
                return "String"

            if op in ["+", "-", "*", "/"]:
                if left_type in ["int", "double"] and right_type in ["int", "double"]:
                    if left_type == "double" or right_type == "double":
                        return "double"
                    return "int"

                self.errors.append(
                    self.format_error(
                        "SEM-004",
                        f"Tipos incompatibles en operación '{op}': '{left_type}' y '{right_type}'",
                        expr.get("line", ""),
                        expr.get("column", "")
                    )
                )
                return None

            if op in [">", "<", ">=", "<="]:
                if left_type in ["int", "double"] and right_type in ["int", "double"]:
                    return "boolean"

                self.errors.append(
                    self.format_error(
                        "SEM-004",
                        f"Comparación inválida entre '{left_type}' y '{right_type}'",
                        expr.get("line", ""),
                        expr.get("column", "")
                    )
                )
                return None

            if op in ["==", "!="]:
                if self.is_assignable(left_type, right_type) or self.is_assignable(right_type, left_type):
                    return "boolean"

                self.errors.append(
                    self.format_error(
                        "SEM-004",
                        f"Comparación inválida entre '{left_type}' y '{right_type}'",
                        expr.get("line", ""),
                        expr.get("column", "")
                    )
                )
                return None

            self.errors.append(
                self.format_error(
                    "SEM-005",
                    f"Operador no soportado: {op}",
                    expr.get("line", ""),
                    expr.get("column", "")
                )
            )
            return None

        return None


def analizador_semantico(ast, symbol_table):
    try:
        analyzer = SemanticAnalyzer()
        analyzer.analyze_program(ast)

        # Devuelve una tabla limpia con símbolos declarados realmente,
        # no solamente identificadores encontrados por el lexer.
        return analyzer.symbol_table, analyzer.errors

    except Exception as e:
        error_detail = {
            "code": "SEM-000",
            "description": f"Error interno en análisis semántico: {str(e)}",
            "line": "",
            "column": ""
        }
        return symbol_table or {}, [error_detail]


# ==================== ANALIZADOR LÉXICO ====================

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

        # Comentarios de una línea
        if codigo[i:i + 2] == "//":
            while i < len(codigo) and codigo[i] != "\n":
                i += 1
                columna += 1
            continue

        # Comentarios multilínea
        if codigo[i:i + 2] == "/*":
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
                errores.append(("ERROR", "Comentario multilínea sin cerrar", linea, columna))

            continue

        # Identificadores y palabras clave
        if es_letra(c):
            inicio = i
            col = columna

            while i < len(codigo) and (es_letra(codigo[i]) or es_numero(codigo[i])):
                i += 1

            lexema = codigo[inicio:i]
            tipo = "KEYWORD" if lexema in KEYWORDS else "IDENTIFICADOR"

            tokens.append((tipo, lexema, linea, col))

            if tipo == "IDENTIFICADOR" and lexema not in tabla_simbolos:
                tabla_simbolos[lexema] = {
                    "tipo": "ID",
                    "linea": linea,
                    "columna": col
                }

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
                else:
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
                tokens.append(("STRING", lexema, linea, col))
            else:
                errores.append(("ERROR", "Cadena sin cerrar", linea, col))

            continue

        # Operadores dobles
        if codigo[i:i + 2] in OPERADORES_DOBLES:
            tokens.append(("OPERADOR", codigo[i:i + 2], linea, columna))
            i += 2
            columna += 2
            continue

        # Operadores simples
        if c in "+-*/=<>!":
            tokens.append(("OPERADOR", c, linea, columna))
            i += 1
            columna += 1
            continue

        # Símbolos
        if c in SIMBOLOS:
            tokens.append(("SIMBOLO", c, linea, columna))
            i += 1
            columna += 1
            continue

        # Error léxico
        errores.append(("ERROR", c, linea, columna))
        i += 1
        columna += 1

    return tokens, errores, tabla_simbolos
