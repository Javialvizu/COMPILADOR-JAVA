# script.py
# Lista de palabras clave del lenguaje de programación
KEYWORDS = { 
    "class", "public", "private", "protected", "static", "final", "void", "int", "float", "double", "if", "else", "for", "while", "do", "switch", "case", "default", "break", "continue", "return", "new", "this", "super"
}

def is_letter(c):
    return c.isalpha() or c == '_'
def is_digit(c):
    return c.isdigit()
# Función para analizar el código fuente y generar una lista de tokens
def analizador_lexico(codigo):

    tokens = []
    i = 0
    line = 1
    column = 0
