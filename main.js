let pyodide;
let pyodideReady = false;
let ultimoTokens = [];
let ultimoErrores = [];
let ultimoSimbolos = {};
let ultimoAST = null;
let ultimoErroresSintacticos = [];
let ultimoErroresSemanticos = [];

// Update status indicator
function updateStatus(message, isReady = false) {
  const statusDot = document.getElementById("status-indicator");
  const statusText = document.getElementById("status-text");
  
  statusText.textContent = message;
  
  if (isReady) {
    statusDot.classList.remove("loading");
    statusDot.style.background = "#10b981";
  } else {
    statusDot.classList.add("loading");
    statusDot.style.background = "#f59e0b";
  }
}

async function iniciarPyodide(){
  try {
    updateStatus("Cargando Pyodide...", false);
    pyodide = await loadPyodide();
    console.log("Pyodide loaded successfully");

    updateStatus("Cargando código Python...", false);
    const response = await fetch("lexer.py");
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    console.log("Fetched lexer.py successfully");

    const codigoPython = await response.text();
    console.log("Got Python code text, length:", codigoPython.length);

    updateStatus("Inicializando compilador...", false);
    await pyodide.runPythonAsync(codigoPython);
    console.log("Python code executed successfully");

    pyodideReady = true;
    updateStatus("Listo para analizar", true);

    document.getElementById("fileInput").addEventListener("change", function(e){
      const file = e.target.files[0];
      if(!file) return;

      const reader = new FileReader();
      reader.onload = function(event){
          document.getElementById("editor").value = event.target.result;
      };
      reader.readAsText(file);
    });

    console.log("Event listener added");

  } catch (e) {
    console.error("Error in iniciarPyodide:", e);
    updateStatus("Error al cargar", false);
    alert("Error al cargar Pyodide o el código Python: " + e.message);
  }
}

iniciarPyodide().catch(console.error);


async function analizar(){
  try {
    if(!pyodideReady){
      alert("Pyodide aún está cargando...");
      return;
    }

    updateStatus("Analizando código...", false);
    const codigo = document.getElementById("editor").value;

    pyodide.globals.set("codigo", codigo);

    let resultado = pyodide.runPython(`analizador_lexico(codigo)`);

    let [tokens, errores, simbolos] = resultado.toJs({
      dict_converter: Object.fromEntries
    });
    ultimoTokens = tokens;
    ultimoErrores = errores;
    ultimoSimbolos = simbolos;

    // Parser
    pyodide.globals.set("tokens", tokens);
    let resultadoParser = pyodide.runPython(`analizador_sintactico(tokens)`);
    let [ast, erroresSintacticos] = resultadoParser.toJs({
      dict_converter: Object.fromEntries
    });
    ultimoAST = ast;
    ultimoErroresSintacticos = erroresSintacticos;

    // Semantic
    pyodide.globals.set("ast", ast);
    pyodide.globals.set("simbolos", simbolos);
    let resultadoSemantic = pyodide.runPython(`analizador_semantico(ast, simbolos)`);
    let [simbolosActualizados, erroresSemanticos] = resultadoSemantic.toJs({
      dict_converter: Object.fromEntries
    });
    ultimoSimbolos = simbolosActualizados;
    ultimoErroresSemanticos = erroresSemanticos;

    mostrarTokens(tokens);
    mostrarErrores(errores);
    mostrarSimbolos(simbolosActualizados);
    mostrarErroresSintacticos(erroresSintacticos);
    mostrarErroresSemanticos(erroresSemanticos);
    mostrarAST(ast);

    updateStatus("Análisis completado", true);

  } catch (e) {
    console.error("Error in analizar:", e);
    updateStatus("Error en el análisis", false);
    alert("Error al analizar: " + e.message);
  }
}

function descargarResultado(){
  ultimoErrores = errores;
  ultimoSimbolos = simbolos;
  mostrarTokens(tokens);
  mostrarErrores(errores);
  mostrarSimbolos(simbolos);
}


function mostrarTokens(tokens){
  let tabla = document.getElementById("tablaTokens");
  tabla.innerHTML="";

  if (tokens.length === 0) {
    tabla.innerHTML = '<tr><td colspan="5" class="empty-state">No hay tokens para mostrar</td></tr>';
    document.getElementById("token-count").textContent = "0 tokens";
    return;
  }

  tokens.forEach((t,i)=>{
    tabla.innerHTML += `
    <tr>
      <td>${i+1}</td>
      <td><span style="color: #818cf8; font-weight: 600;">${t[0]}</span></td>
      <td><code>${t[1]}</code></td>
      <td>${t[2]}</td>
      <td>${t[3]}</td>
    </tr>`;
  });

  document.getElementById("token-count").textContent = `${tokens.length} tokens`;
}


function mostrarErrores(errores){
  let tabla = document.getElementById("tablaErrores");
  tabla.innerHTML="";

  if (errores.length === 0) {
    tabla.innerHTML = '<tr><td colspan="4" class="empty-state success">✓ Sin errores léxicos</td></tr>';
    document.getElementById("lex-error-count").textContent = "0 errores";
    return;
  }

  errores.forEach(e=>{
    tabla.innerHTML += `
    <tr>
      <td><span style="color: #ef4444; font-weight: 600;">${e[0]}</span></td>
      <td><code>${e[1]}</code></td>
      <td>${e[2]}</td>
      <td>${e[3]}</td>
    </tr>`;
  });

  document.getElementById("lex-error-count").textContent = `${errores.length} errores`;
}


function mostrarSimbolos(simbolos){
  let tabla = document.getElementById("tablaSimbolos");
  tabla.innerHTML="";

  const entries = Object.entries(simbolos);
  
  if (entries.length === 0) {
    tabla.innerHTML = '<tr><td colspan="3" class="empty-state">Sin símbolos identificados</td></tr>';
    document.getElementById("symbol-count").textContent = "0 símbolos";
    return;
  }

  entries.forEach(([id, data])=>{
    tabla.innerHTML += `
    <tr>
      <td><code style="color: #10b981; font-weight: 600;">${id}</code></td>
      <td><span style="color: #818cf8;">${data.tipo || 'ID'}</span></td>
      <td>${data.linea}</td>
    </tr>`;
  });

  document.getElementById("symbol-count").textContent = `${entries.length} símbolos`;
}

function parseErrorDetail(error) {
  if (!error) return { description: '', line: '', column: '' };
  if (Array.isArray(error) && error.length >= 4) {
    return { description: error[0], line: error[2], column: error[3] };
  }

  const detalle = String(error);
  const regex = /(.+?)\s+en línea\s+(\d+)(?:\s+columna\s+(\d+))?$/;
  const match = detalle.match(regex);
  if (match) {
    return { description: match[1].trim(), line: match[2], column: match[3] || '' };
  }

  return { description: detalle, line: '', column: '' };
}

function mostrarErroresSintacticos(errores){
  let tabla = document.getElementById("tablaErroresSintacticos");
  tabla.innerHTML="";

  if (errores.length === 0) {
    tabla.innerHTML = '<tr><td class="empty-state success" colspan="3">✓ Sin errores sintácticos</td></tr>';
    document.getElementById("sint-error-count").textContent = "0 errores";
    return;
  }

  errores.forEach(e=>{
    const detalle = parseErrorDetail(e);
    tabla.innerHTML += `
    <tr>
      <td><span style="color: #fca5a5;">${detalle.description}</span></td>
      <td>${detalle.line}</td>
      <td>${detalle.column}</td>
    </tr>`;
  });

  document.getElementById("sint-error-count").textContent = `${errores.length} errores`;
}

function mostrarErroresSemanticos(errores){
  let tabla = document.getElementById("tablaErroresSemanticos");
  tabla.innerHTML="";

  if (errores.length === 0) {
    tabla.innerHTML = '<tr><td class="empty-state success" colspan="3">✓ Sin errores semánticos</td></tr>';
    document.getElementById("sem-error-count").textContent = "0 errores";
    return;
  }

  errores.forEach(e=>{
    const detalle = parseErrorDetail(e);
    tabla.innerHTML += `
    <tr>
      <td><span style="color: #fca5a5;">${detalle.description}</span></td>
      <td>${detalle.line}</td>
      <td>${detalle.column}</td>
    </tr>`;
  });

  document.getElementById("sem-error-count").textContent = `${errores.length} errores`;
}

function mostrarAST(ast){
  let div = document.getElementById("astDisplay");
  if(ast){
    div.innerHTML = renderAST(ast);
  } else {
    div.innerHTML = '<div class="empty-state">No se pudo generar el AST.</div>';
  }
}

function renderAST(node, indent = 0, maxDepth = 10){
  if(!node || typeof node !== 'object' || indent > maxDepth) return '';

  let html = '<ul>';
  for(let key in node){
    html += '<li>';
    if(typeof node[key] === 'object' && node[key] !== null){
      html += `<span class="ast-node">${key}:</span> <button class="toggle-btn" onclick="toggle(this)">+</button><div class="nested hidden">${renderAST(node[key], indent + 1, maxDepth)}</div>`;
    } else {
      html += `<span class="ast-leaf">${key}: ${node[key]}</span>`;
    }
    html += '</li>';
  }
  html += '</ul>';
  return html;
}

function showTab(tabId) {
  // Hide all tab panels
  const panels = document.querySelectorAll('.tab-panel');
  panels.forEach(panel => panel.classList.remove('active'));

  // Remove active class from all buttons
  const buttons = document.querySelectorAll('.tab-button');
  buttons.forEach(button => button.classList.remove('active'));

  // Show the selected tab panel
  document.getElementById(tabId + '-tab').classList.add('active');

  // Add active class to the clicked button
  event.target.classList.add('active');
}

function toggle(btn){
  let div = btn.nextElementSibling;
  if(div.classList.contains('hidden')){
    div.classList.remove('hidden');
    btn.textContent = '-';
  } else {
    div.classList.add('hidden');
    btn.textContent = '+';
  }
}

function descargarResultado(){
  if(ultimoTokens.length === 0){
    alert("Primero debes analizar el código.");
    return;
  }

  let contenido = "===== RESULTADO COMPILADOR JAVA =====\n\n";

  // TOKENS
  contenido += "---- TOKENS ----\n";
  contenido += "No.\tTipo\tLexema\tLinea\tColumna\n";

  ultimoTokens.forEach((t,i)=>{
    contenido += `${i+1}\t${t[0]}\t${t[1]}\t${t[2]}\t${t[3]}\n`;
  });

  // ERRORES LEXICOS
  contenido += "\n---- ERRORES LEXICOS ----\n";

  if(ultimoErrores.length === 0){
    contenido += "No se encontraron errores.\n";
  } else {
    ultimoErrores.forEach(e=>{
      contenido += `${e[0]}\t${e[1]}\t${e[2]}\t${e[3]}\n`;
    });
  }

  // ERRORES SINTACTICOS
  contenido += "\n---- ERRORES SINTACTICOS ----\n";

  if(ultimoErroresSintacticos.length === 0){
    contenido += "No se encontraron errores.\n";
  } else {
    ultimoErroresSintacticos.forEach(e=>{
      contenido += `${e}\n`;
    });
  }

  // AST
  contenido += "\n---- ARBOL DE SINTAXIS ABSTRACTA (AST) ----\n";
  if(ultimoAST){
    contenido += JSON.stringify(ultimoAST, null, 2) + "\n";
  } else {
    contenido += "No se pudo generar el AST.\n";
  }

  // ERRORES SEMANTICOS
  contenido += "\n---- ERRORES SEMANTICOS ----\n";

  if(ultimoErroresSemanticos.length === 0){
    contenido += "No se encontraron errores.\n";
  } else {
    ultimoErroresSemanticos.forEach(e=>{
      contenido += `${e}\n`;
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
  a.download = "resultado_compilador.txt";
  a.click();

  URL.revokeObjectURL(url);
}

// Asignar funciones globales
window.analizar = analizar;
window.descargarResultado = descargarResultado;
window.toggle = toggle;
window.showTab = showTab;
window.exportarASTImagen = exportarASTImagen;
window.exportarASTPDF = exportarASTPDF;

/* ==================== EXPORT FUNCTIONS ==================== */

async function exportarASTImagen() {
  try {
    const astContainer = document.getElementById('astDisplay');
    
    if (!ultimoAST) {
      alert('Por favor, analiza el código primero para generar el AST.');
      return;
    }

    // Crear un elemento temporal con mejor estilo para captura
    const tempContainer = document.createElement('div');
    tempContainer.style.cssText = `
      background: #1e293b;
      padding: 30px;
      border-radius: 12px;
      position: fixed;
      top: -9999px;
      left: -9999px;
      max-width: 1200px;
      color: #f1f5f9;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      z-index: 10000;
    `;
    
    // Crear header
    const header = document.createElement('div');
    header.style.cssText = `
      text-align: center;
      margin-bottom: 30px;
      border-bottom: 2px solid #6366f1;
      padding-bottom: 20px;
    `;
    header.innerHTML = `
      <h1 style="margin: 0; color: #818cf8; font-size: 28px;">Árbol de Sintaxis Abstracta (AST)</h1>
      <p style="margin: 10px 0 0 0; color: #cbd5e1; font-size: 14px;">Compilador Java - Generado: ${new Date().toLocaleString('es-ES')}</p>
    `;
    
    // Copiar el contenido del AST
    const astContent = document.createElement('div');
    astContent.innerHTML = astContainer.innerHTML;
    astContent.style.cssText = `
      font-size: 14px;
      line-height: 1.6;
    `;
    
    tempContainer.appendChild(header);
    tempContainer.appendChild(astContent);
    document.body.appendChild(tempContainer);

    // Capturar como imagen
    const canvas = await html2canvas(tempContainer, {
      backgroundColor: '#1e293b',
      scale: 2,
      logging: false,
      useCORS: true,
      allowTaint: true
    });

    // Descargar imagen
    canvas.toBlob(function(blob) {
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `AST_${Date.now()}.png`;
      link.click();
      URL.revokeObjectURL(url);
      
      // Limpiar
      document.body.removeChild(tempContainer);
      
      // Notification
      mostrarNotificacion('✓ AST exportado a PNG exitosamente', 'success');
    });
    
  } catch (e) {
    console.error('Error al exportar AST como imagen:', e);
    mostrarNotificacion('Error al exportar imagen: ' + e.message, 'error');
  }
}

async function exportarASTPDF() {
  try {
    if (!ultimoAST) {
      alert('Por favor, analiza el código primero para generar el AST.');
      return;
    }

    const astContainer = document.getElementById('astDisplay');
    
    // Crear un elemento temporal con mejor estilo
    const tempContainer = document.createElement('div');
    tempContainer.style.cssText = `
      background: white;
      padding: 40px;
      position: fixed;
      top: -9999px;
      left: -9999px;
      max-width: 800px;
      color: #1a202c;
      font-family: 'Courier New', monospace;
      font-size: 12px;
      z-index: 10000;
    `;
    
    // Crear header
    const header = document.createElement('div');
    header.style.cssText = `
      text-align: center;
      margin-bottom: 30px;
      border-bottom: 3px solid #6366f1;
      padding-bottom: 20px;
    `;
    header.innerHTML = `
      <h1 style="margin: 0; color: #6366f1; font-size: 24px; font-family: 'Segoe UI', sans-serif;">Árbol de Sintaxis Abstracta (AST)</h1>
      <p style="margin: 10px 0 0 0; color: #718096; font-size: 12px;">Compilador Java | ${new Date().toLocaleString('es-ES')}</p>
    `;
    
    // Copiar contenido del AST
    const astContent = document.createElement('div');
    astContent.innerHTML = astContainer.innerHTML;
    astContent.style.cssText = `
      color: #1a202c;
      line-height: 1.5;
      word-break: break-word;
    `;
    
    // Cambiar colores para PDF
    const nodes = astContent.querySelectorAll('.ast-node');
    const leaves = astContent.querySelectorAll('.ast-leaf');
    
    nodes.forEach(node => {
      node.style.color = '#6366f1';
      node.style.fontWeight = 'bold';
    });
    
    leaves.forEach(leaf => {
      leaf.style.color = '#059669';
    });

    tempContainer.appendChild(header);
    tempContainer.appendChild(astContent);
    document.body.appendChild(tempContainer);

    // Capturar como canvas
    const canvas = await html2canvas(tempContainer, {
      backgroundColor: 'white',
      scale: 2,
      logging: false,
      useCORS: true,
      allowTaint: true
    });

    // Calcular dimensiones para PDF
    const imgData = canvas.toDataURL('image/png');
    const imgWidth = 210; // A4 width en mm
    const imgHeight = (canvas.height * imgWidth) / canvas.width;
    
    const {jsPDF} = window.jspdf;
    const pdf = new jsPDF({
      orientation: imgHeight > imgWidth ? 'portrait' : 'portrait',
      unit: 'mm',
      format: 'a4'
    });
    
    let heightLeft = imgHeight;
    let position = 0;

    // Agregar páginas si es necesario
    pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
    heightLeft -= 297; // altura de una página A4
    
    while (heightLeft >= 0) {
      position = heightLeft - imgHeight;
      pdf.addPage();
      pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
      heightLeft -= 297;
    }

    // Descargar PDF
    pdf.save(`AST_${Date.now()}.pdf`);
    
    // Limpiar
    document.body.removeChild(tempContainer);
    
    // Notification
    mostrarNotificacion('✓ AST exportado a PDF exitosamente', 'success');
    
  } catch (e) {
    console.error('Error al exportar AST como PDF:', e);
    mostrarNotificacion('Error al exportar PDF: ' + e.message, 'error');
  }
}

// Función para mostrar notificaciones
function mostrarNotificacion(mensaje, tipo = 'info') {
  const notification = document.createElement('div');
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 15px 25px;
    border-radius: 8px;
    font-weight: 600;
    z-index: 10001;
    animation: slideInRight 0.3s ease;
    max-width: 400px;
  `;
  
  if (tipo === 'success') {
    notification.style.background = '#10b981';
    notification.style.color = 'white';
  } else if (tipo === 'error') {
    notification.style.background = '#ef4444';
    notification.style.color = 'white';
  } else {
    notification.style.background = '#3b82f6';
    notification.style.color = 'white';
  }
  
  notification.textContent = mensaje;
  document.body.appendChild(notification);
  
  // Remover después de 3 segundos
  setTimeout(() => {
    notification.style.animation = 'slideOutRight 0.3s ease';
    setTimeout(() => {
      document.body.removeChild(notification);
    }, 300);
  }, 3000);
}

// Agregar animaciones
const style = document.createElement('style');
style.textContent = `
  @keyframes slideInRight {
    from {
      transform: translateX(400px);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }
  
  @keyframes slideOutRight {
    from {
      transform: translateX(0);
      opacity: 1;
    }
    to {
      transform: translateX(400px);
      opacity: 0;
    }
  }
`;
document.head.appendChild(style);