let pyodide;
let pyodideReady = false;
let ultimoTokens = [];
let ultimoErrores = [];
let ultimoSimbolos = {};

async function iniciarPyodide(){
  pyodide = await loadPyodide();

  const response = await fetch("lexer.py");
  const codigoPython = await response.text();

  await pyodide.runPythonAsync(codigoPython);

  pyodideReady = true;
}

iniciarPyodide();


// 📂 INPUT FILE (VA FUERA DE ANALIZAR)
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
  ultimoTokens = tokens;
  ultimoErrores = errores;
  ultimoSimbolos = simbolos;
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
function descargarResultado(){

  if(ultimoTokens.length === 0){
    alert("Primero debes analizar el código.");
    return;
  }

  let contenido = "===== RESULTADO ANALIZADOR LEXICO JAVA =====\n\n";

  // TOKENS
  contenido += "---- TOKENS ----\n";
  contenido += "No.\tTipo\tLexema\tLinea\tColumna\n";

  ultimoTokens.forEach((t,i)=>{
    contenido += `${i+1}\t${t[0]}\t${t[1]}\t${t[2]}\t${t[3]}\n`;
  });

  // ERRORES
  contenido += "\n---- ERRORES LEXICOS ----\n";

  if(ultimoErrores.length === 0){
    contenido += "No se encontraron errores.\n";
  } else {
    ultimoErrores.forEach(e=>{
      contenido += `${e[0]}\t${e[1]}\t${e[2]}\t${e[3]}\n`;
    });
  }

  // TABLA DE SIMBOLOS
  contenido += "\n---- TABLA DE SIMBOLOS ----\n";
  contenido += "Identificador\tTipo\tLinea\n";

  Object.entries(ultimoSimbolos).forEach(([id,data])=>{
    contenido += `${id}\t${data.tipo}\t${data.linea}\n`;
  });

  // CREAR ARCHIVO
  const blob = new Blob([contenido], { type: "text/plain" });
  const url = URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = "resultado_analizador.txt";
  a.click();

  URL.revokeObjectURL(url);
}