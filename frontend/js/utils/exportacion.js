import { ReportesAPI, FORMATOS_EXPORTACION } from "../api/inventario_api.js";
import { descargarArchivo } from "./helpers.js";

export function conectarExportacion(reporte, obtenerFiltros = () => ({})) {
    const contenedor = document.getElementById("menu-exportar");
    if (!contenedor) return;

    contenedor.innerHTML = `
        <div class="dropdown">
            <button class="btn btn-sm btn-outline-secondary dropdown-toggle" id="btn-exportar"
                    data-bs-toggle="dropdown" aria-expanded="false">
                <i class="bi bi-download me-1"></i>Exportar
            </button>
            <ul class="dropdown-menu dropdown-menu-end">
                ${FORMATOS_EXPORTACION.map((f) => `
                <li><button class="dropdown-item" type="button" data-formato="${f.formato}">
                    <i class="bi ${f.icono} me-2"></i>${f.etiqueta}</button></li>`).join("")}
            </ul>
        </div>`;

    const boton = document.getElementById("btn-exportar");
    contenedor.querySelectorAll("[data-formato]").forEach((item) =>
        item.addEventListener("click", () =>
            descargarArchivo(ReportesAPI.urlExportar(reporte, item.dataset.formato, obtenerFiltros()), boton)));
}
