/* static/js/logica.js */

const API_URL = 'http://127.0.0.1:5000';

// --- EVENTO INICIAL (Cuando carga la página) ---
document.addEventListener('DOMContentLoaded', () => {
    cargarListas('/materias', 'selectMateria');
    cargarListas('/carreras', 'selectCarrera');
    cargarGrafico(); // <--- AGREGAR ESTO
    verificarSesion();
});

// --- FUNCIÓN GENÉRICA PARA LLENAR DROPDOWNS ---
async function cargarListas(endpoint, elementoId) {
    const select = document.getElementById(elementoId);
    try {
        const res = await fetch(API_URL + endpoint);
        const datos = await res.json();
        
        select.innerHTML = '<option value="" disabled selected>-- Seleccionar --</option>';
        datos.forEach(item => {
            const opt = document.createElement('option');
            opt.text = item.nombre || item.nombre_carrera; 
            opt.value = endpoint === '/materias' ? item.nombre : item.id; 
            select.appendChild(opt);
        });
    } catch (e) { console.error("Error cargando lista:", e); }
}

// --- ACCIÓN 1: REGISTRAR ESTUDIANTE ---
async function registrarEstudiante() {
    const nombre = document.getElementById('nombreNuevo').value;
    const apellido = document.getElementById('apellidoNuevo').value;
    const idCarrera = document.getElementById('selectCarrera').value;
    const divRes = document.getElementById('resRegistro');

    if(!nombre || !apellido || !idCarrera) {
        divRes.innerHTML = `<div class="msg error">Llena todos los campos</div>`;
        return;
    }

    try {
        const res = await fetch(API_URL + '/estudiantes', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ nombre, apellido, id_carrera: idCarrera })
        });
        const data = await res.json();
        const clase = data.status === 'success' ? 'success' : 'error';
        divRes.innerHTML = `<div class="msg ${clase}">${data.mensaje}</div>`;
        
    } catch (e) { divRes.innerHTML = `<div class="msg error">Error de conexión</div>`; }
}

// --- ACCIÓN 2: INSCRIBIR MATERIA ---
async function realizarInscripcion() {
    const id = document.getElementById('idInscribir').value;
    const materia = document.getElementById('selectMateria').value;
    const divRes = document.getElementById('resInscripcion');

    try {
        const res = await fetch(API_URL + '/inscribir', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ id_estudiante: id, materia: materia })
        });
        const data = await res.json();
        const clase = data.status === 'success' ? 'success' : 'error';
        divRes.innerHTML = `<div class="msg ${clase}">${data.mensaje}</div>`;
    } catch (e) { divRes.innerHTML = `<div class="msg error">Error de conexión</div>`; }
}

// --- ACCIÓN 3: CONSULTAR NOTAS ---
async function buscarNotas() {
    const id = document.getElementById('idBuscar').value;
    const divRes = document.getElementById('resConsulta');
    divRes.innerHTML = "Cargando...";
    
    try {
        const res = await fetch(`${API_URL}/notas/${id}`);
        const data = await res.json();

        if (data.status === 'success') {
            const nombre = data.data[0].Apellido;
            const honor = data.data[0].Honor_Actual;
            
            let html = `
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                    <div><b>${nombre}</b> <span style="font-size:0.8em; color:#666">(${honor})</span></div>
                    <button class="btn-red" onclick="eliminarEstudiante(${id})" style="width:auto; padding:5px 10px; font-size:0.8rem;">Dar de Baja</button>
                </div>
                <table>`;
            
            data.data.forEach(fila => {
                html += `<tr><td>${fila.Materia}</td><td><b>${fila.nota}</b></td></tr>`;
            });
            html += `</table>`;
            divRes.innerHTML = html;
        } else {
            divRes.innerHTML = `<div class="msg error">${data.mensaje}</div>`;
        }
    } catch (e) { divRes.innerHTML = `<div class="msg error">Estudiante no encontrado</div>`; }
}

// --- ACCIÓN 4: ELIMINAR (SOFT DELETE) ---
async function eliminarEstudiante(id) {
    if(!confirm("¿Seguro que quieres dar de baja a este estudiante?")) return;

    try {
        const res = await fetch(`${API_URL}/estudiantes/${id}`, { method: 'DELETE' });
        const data = await res.json();
        alert(data.mensaje);
        if(data.status === 'success') document.getElementById('resConsulta').innerHTML = '';
    } catch (e) { alert("Error al conectar con el servidor"); }
}

// --- ACCIÓN 5: AUDITORÍA ---
async function cargarAuditoria() {
    const divTabla = document.getElementById('tablaAuditoria');
    divTabla.innerHTML = "Cargando...";

    try {
        const res = await fetch(API_URL + '/auditoria');
        const logs = await res.json();

        if (logs.length === 0) {
            divTabla.innerHTML = "<p>✅ Sin novedades.</p>";
            return;
        }

        let html = `
            <table style="font-size: 0.85rem;">
                <tr style="background-color: #ffe6e6;">
                    <th>Fecha</th><th>Estudiante</th><th>Antes</th><th>Ahora</th><th>Usuario</th>
                </tr>`;

        logs.forEach(log => {
            const color = log.NotaNueva < log.NotaAnterior ? 'red' : 'green';
            html += `
                <tr>
                    <td>${log.Fecha}</td>
                    <td><b>${log.Estudiante}</b></td>
                    <td style="color: grey">${log.NotaAnterior}</td>
                    <td style="color: ${color}; font-weight:bold">${log.NotaNueva}</td>
                    <td>${log.Usuario}</td>
                </tr>`;
        });
        divTabla.innerHTML = html + "</table>";

    } catch (e) { console.error(e); divTabla.innerHTML = "Error al cargar logs."; }
}
// --- ACCIÓN 6: DESCARGAR EXCEL ---
function descargarExcel() {
    // Redireccionamos al navegador a la ruta de descarga
    // El navegador manejará la descarga automáticamente
    window.location.href = API_URL + '/reporte/excel';
}

// --- ACCIÓN 7: BÚSQUEDA EN VIVO (LIVE SEARCH) ---

// 1. Seleccionamos el input
const inputBusqueda = document.getElementById('inputBusqueda');
const divResultados = document.getElementById('listaResultados');

// 2. Agregamos el "Escuchador" de eventos
// 'input' se dispara cada vez que cambia el texto (escribir o borrar)
if(inputBusqueda){
    inputBusqueda.addEventListener('input', async function() {
        const texto = this.value;

        // Si borró todo, limpiamos la lista
        if (texto.length === 0) {
            divResultados.innerHTML = '';
            return;
        }

        try {
            // 3. Llamamos a la API con el texto (?q=juan)
            const res = await fetch(`${API_URL}/estudiantes/buscar?q=${texto}`);
            const resultados = await res.json();

            // 4. Renderizamos la lista
            if (resultados.length > 0) {
                let html = `<ul style="list-style:none; padding:0;">`;
                
                resultados.forEach(est => {
                    html += `
                        <li style="padding:10px; border-bottom:1px solid #eee; display:flex; justify-content:space-between; align-items:center;">
                            <div>
                                <strong>${est.nombre_completo}</strong>
                                <br><small style="color:#888">${est.carrera}</small>
                            </div>
                            <button onclick="copiarID(${est.id})" style="width:auto; padding:5px; font-size:0.7rem; background:#3498db;">
                                Usar ID: ${est.id}
                            </button>
                        </li>
                    `;
                });
                html += `</ul>`;
                divResultados.innerHTML = html;
            } else {
                divResultados.innerHTML = `<p style="color:#888; padding:10px;">No se encontraron estudiantes.</p>`;
            }

        } catch (e) {
            console.error(e);
        }
    });
}

// Función auxiliar para facilitar la vida al usuario
function copiarID(id) {
    // Rellena los otros inputs con este ID automáticamente
    document.getElementById('idBuscar').value = id;
    document.getElementById('idInscribir').value = id;
    alert(`ID ${id} seleccionado. Ve a 'Consultar' o 'Inscribir'.`);
}

// --- ACCIÓN 8: DIBUJAR GRÁFICO (CHART.JS) ---
async function cargarGrafico() {
    try {
        // 1. Pedimos los datos numéricos a Python
        const res = await fetch(API_URL + '/estadisticas/carreras');
        const datos = await res.json();

        // 2. Buscamos el lienzo (canvas) en el HTML
        const ctx = document.getElementById('graficoCarreras').getContext('2d');

        // 3. Creamos el Gráfico
        // Chart es una clase que viene de la librería que importamos
        new Chart(ctx, {
            type: 'doughnut', // Tipo de gráfico: 'bar', 'line', 'pie', 'doughnut'
            data: {
                labels: datos.etiquetas, // Ej: ['Sistemas', 'Derecho']
                datasets: [{
                    label: 'Estudiantes Inscritos',
                    data: datos.valores, // Ej: [10, 5]
                    backgroundColor: [
                        '#4a90e2', // Azul
                        '#50e3c2', // Verde
                        '#e74c3c', // Rojo
                        '#f1c40f', // Amarillo
                        '#8e44ad'  // Morado
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'right' }
                }
            }
        });

    } catch (e) {
        console.error("Error cargando gráfico:", e);
    }
}

// --- ACCIÓN 9: LOGIN ---
async function hacerLogin() {
    const user = document.getElementById('loginUser').value;
    const pass = document.getElementById('loginPass').value;
    const msg = document.getElementById('msgLogin');

    try {
        const res = await fetch(API_URL + '/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ usuario: user, password: pass })
        });
        const data = await res.json();

        if (data.status === 'success') {
            // 1. Ocultamos la pantalla de Login
            document.getElementById('loginOverlay').style.display = 'none';
            // 2. Mostramos botón de salir
            // 2. MOSTRAMOS LA APP PRINCIPAL (¡Esto es lo nuevo!)
            // Usamos 'grid' porque en tu CSS la clase .container usa display: grid
            document.getElementById('appPrincipal').style.display = 'grid';
            document.getElementById('btnSalir').style.display = 'block';
            
            // 3. Guardamos el rol en el navegador para usarlo luego
            localStorage.setItem('rolUsuario', data.rol);
            
            // TRUCO DE PRO: Si no es Admin, ocultamos cosas peligrosas
            if(data.rol !== 'Admin') {
                // Ocultamos Auditoría y Botones de borrar (esto es solo visual)
                // En un sistema real, el Backend también debe bloquearlo.
                const auditoriaCard = document.querySelector('.card[style*="e74c3c"]'); // Tarjeta roja
                if(auditoriaCard) auditoriaCard.style.display = 'none';
            }

            alert(data.mensaje);
        } else {
            msg.innerHTML = `<div class="msg error">${data.mensaje}</div>`;
        }
    } catch (e) {
        msg.innerHTML = `<div class="msg error">Error de conexión</div>`;
    }
}

// --- ACCIÓN 10: LOGOUT ---
async function hacerLogout() {
    await fetch(API_URL + '/logout');
    localStorage.removeItem('rolUsuario'); // BORRAMOS EL RASTRO DEL NAVEGADOR
    location.reload(); // Recargamos la página para volver a bloquear
}

// --- FUNCIÓN NUEVA 11 : Verificar si ya estoy logueado ---
async function verificarSesion() {
    // Truco: Preguntamos al rol guardado en localStorage
    const rolGuardado = localStorage.getItem('rolUsuario');

    if (rolGuardado) {
        // Si hay un rol guardado, asumimos que está logueado y abrimos el telón
        document.getElementById('loginOverlay').style.display = 'none';
        document.getElementById('appPrincipal').style.display = 'grid';
        document.getElementById('btnSalir').style.display = 'block';

        // Aplicamos las reglas visuales (Admin vs Invitado)
        if(rolGuardado !== 'Admin') {
            const auditoriaCard = document.querySelector('.card[style*="e74c3c"]');
            if(auditoriaCard) auditoriaCard.style.display = 'none';
        }
        
        // Cargamos el gráfico (solo si ya entró)
        cargarGrafico();
    }
}
