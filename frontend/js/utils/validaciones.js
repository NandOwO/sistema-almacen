const PATRON_TEXTO = /^[A-Za-zÁÉÍÓÚÜáéíóúüÑñ .,'\-]+$/;
const PATRON_USUARIO = /^[A-Za-z0-9._-]+$/;
const PATRON_CORREO = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
const PATRON_DIGITOS = /^\d+$/;

export function requerido(valor, campo) {
    if (!valor || !valor.trim()) return `El campo '${campo}' es obligatorio.`;
    return null;
}

export function soloTexto(valor, campo, { obligatorio = true } = {}) {
    valor = (valor || "").trim();
    if (!valor) return obligatorio ? `El campo '${campo}' es obligatorio.` : null;
    if (!PATRON_TEXTO.test(valor)) return `El campo '${campo}' solo admite letras y espacios.`;
    return null;
}

export function usuario(valor) {
    valor = (valor || "").trim();
    if (valor.length < 3) return "El usuario debe tener al menos 3 caracteres.";
    if (!PATRON_USUARIO.test(valor))
        return "El usuario solo admite letras, números, punto, guion y guion bajo.";
    return null;
}

export function correo(valor, { obligatorio = false } = {}) {
    valor = (valor || "").trim();
    if (!valor) return obligatorio ? "El correo es obligatorio." : null;
    if (!PATRON_CORREO.test(valor)) return "El correo no tiene un formato válido.";
    return null;
}

export function digitos(valor, campo, { longitud = null, obligatorio = false } = {}) {
    valor = (valor || "").trim();
    if (!valor) return obligatorio ? `El campo '${campo}' es obligatorio.` : null;
    if (!PATRON_DIGITOS.test(valor)) return `El campo '${campo}' solo admite números.`;
    if (longitud && valor.length !== longitud)
        return `El campo '${campo}' debe tener ${longitud} dígitos.`;
    return null;
}

export function claveMinima(valor, { obligatorio = true, minimo = 4 } = {}) {
    valor = valor || "";
    if (!valor) return obligatorio ? "La clave es obligatoria." : null;
    if (valor.length < minimo) return `La clave debe tener al menos ${minimo} caracteres.`;
    return null;
}

export function noNegativo(valor, campo) {
    if (valor === "" || valor === null || valor === undefined)
        return `El campo '${campo}' es obligatorio.`;
    const numero = Number(valor);
    if (Number.isNaN(numero)) return `El campo '${campo}' debe ser un número.`;
    if (numero < 0) return `El campo '${campo}' no puede ser negativo.`;
    return null;
}

export function primerError(errores) {
    return errores.find((e) => e) || null;
}

const PREFIJOS_RUC = ["10", "15", "16", "17", "20"];
const PESOS_RUC = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2];

export function ruc(valor, { obligatorio = false } = {}) {
    valor = (valor || "").trim();
    if (!valor) return obligatorio ? "El RUC es obligatorio." : null;
    if (!PATRON_DIGITOS.test(valor) || valor.length !== 11) return "El RUC debe tener 11 dígitos.";
    if (!PREFIJOS_RUC.includes(valor.slice(0, 2))) return "El RUC debe empezar con 10, 15, 16, 17 o 20.";
    const suma = PESOS_RUC.reduce((acc, peso, i) => acc + Number(valor[i]) * peso, 0);
    let verificador = 11 - (suma % 11);
    if (verificador === 10) verificador = 0;
    else if (verificador === 11) verificador = 1;
    if (verificador !== Number(valor[10])) return "El RUC no es válido (dígito verificador incorrecto).";
    return null;
}

export function telefono(valor, { obligatorio = false } = {}) {
    valor = (valor || "").trim();
    if (!valor) return obligatorio ? "El teléfono es obligatorio." : null;
    if (!PATRON_DIGITOS.test(valor)) return "El teléfono solo admite números.";
    if (valor.length !== 9) return "El teléfono debe tener 9 dígitos.";
    return null;
}

export function hoyISO() {
    return new Date().toISOString().slice(0, 10);
}

export function fechaNoPasada(valor, campo = "Fecha de vencimiento") {
    if (!valor) return null;
    if (valor < hoyISO()) return `El campo '${campo}' no puede ser una fecha pasada.`;
    return null;
}

export function rangoFechas(desde, hasta) {
    if (desde && hasta && desde > hasta) {
        return "La fecha 'Desde' no puede ser mayor que 'Hasta'.";
    }
    return null;
}

export function filtrarEntrada(input, tipo) {
    const patrones = {
        texto: /[^A-Za-zÁÉÍÓÚÜáéíóúüÑñ .,'\-]/g,
        usuario: /[^A-Za-z0-9._-]/g,
        digitos: /[^\d]/g,
    };
    input.addEventListener("input", () => {
        const limpio = input.value.replace(patrones[tipo], "");
        if (limpio !== input.value) input.value = limpio;
    });
}

export function soloNumero(input, permitirDecimal = false) {
    if (!input) return;
    const bloqueadas = permitirDecimal
        ? ["e", "E", "+", "-", ","]
        : ["e", "E", "+", "-", ",", "."];
    input.addEventListener("keydown", (ev) => {
        if (bloqueadas.includes(ev.key)) ev.preventDefault();
    });
    input.addEventListener("paste", (ev) => {
        const texto = (ev.clipboardData || window.clipboardData).getData("text");
        const patron = permitirDecimal ? /^\d*\.?\d*$/ : /^\d*$/;
        if (!patron.test(texto)) ev.preventDefault();
    });
}
