let pyodide;

async function iniciarPyodide(){
  pyodide = await loadPyodide();

  const response = await fetch("lexer.py");
  const codigoPython = await response.text();

  await pyodide.runPythonAsync(codigoPython);
}

iniciarPyodide();

async function analizar(){

  const codigo = document.getElementById("editor").value;

  pyodide.globals.set("codigo", codigo);

  let resultado = pyodide.runPython(`analizador_lexico(codigo)`);

  let [tokens, errores, simbolos] = resultado.toJs({
    dict_converter: Object.fromEntries
  });

  mostrarTokens(tokens);
  mostrarErrores(errores);
  mostrarSimbolos(simbolos);
}

function mostrarTokens(tokens){
  let tabla = document.getElementById("tablaTokens");
  tabla.innerHTML="";

  tokens.forEach((t,i)=>{
    tabla.innerHTML += `
    <tr>
      <td>${i+1}</td>
      <td>${t[0]}</td>
      <td>${t[1]}</td>
      <td>${t[2]}</td>
      <td>${t[3]}</td>
    </tr>`;
  });
}

function mostrarErrores(errores){
  let tabla = document.getElementById("tablaErrores");
  tabla.innerHTML="";

  errores.forEach(e=>{
    tabla.innerHTML += `
    <tr>
      <td>${e[0]}</td>
      <td>${e[1]}</td>
      <td>${e[2]}</td>
      <td>${e[3]}</td>
    </tr>`;
  });
}

function mostrarSimbolos(simbolos){
  let tabla = document.getElementById("tablaSimbolos");
  tabla.innerHTML="";

  Object.entries(simbolos).forEach(([id, data])=>{
    tabla.innerHTML += `
    <tr>
      <td>${id}</td>
      <td>${data.tipo}</td>
      <td>${data.linea}</td>
    </tr>`;
  });
}