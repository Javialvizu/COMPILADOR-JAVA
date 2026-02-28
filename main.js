let pyodide;
let pyodideReady = false;

async function iniciarPyodide(){
  pyodide = await loadPyodide();

  const response = await fetch("lexer.py");
  const codigoPython = await response.text();

  await pyodide.runPythonAsync(codigoPython);

  pyodideReady = true;
}

iniciarPyodide();


document.getElementById("fileInput").addEventListener("change", function(e){

  const file = e.target.files[0];
  if(!file) return;

  const reader = new FileReader();

  reader.onload = function(event){
      document.getElementById("editor").value = event.target.result;
  };

  reader.readAsText(file);
});


// ▶️ ANALIZAR
async function analizar(){

  if(!pyodideReady){
    alert("Pyodide aún está cargando...");
    return;
  }

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


// 🧾 TOKENS
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


// ❌ ERRORES
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


// 🧠 TABLA DE SÍMBOLOS
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