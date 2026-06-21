/* ==========================================================================
   Bitacora - filtros avanzados (carga dinamica de opciones)
   ==========================================================================
   Consume el endpoint `bitacora_opciones_filtros` y rellena los selects.
   Su uso es opcional: por defecto los selects estan poblados desde
   el contexto del template. Este script existe para poder refrescar las
   opciones sin recargar la pagina.
*/

(function () {
    "use strict";

    var ENDPOINT = "/bitacora/api/opciones-filtros/";

    function fillSelect(selectEl, items, placeholder) {
        if (!selectEl) {
            return;
        }
        var current = selectEl.value;
        selectEl.innerHTML = "";

        var opt = document.createElement("option");
        opt.value = "";
        opt.textContent = placeholder || "Todos";
        selectEl.appendChild(opt);

        items.forEach(function (item) {
            var o = document.createElement("option");
            if (typeof item === "string") {
                o.value = item;
                o.textContent = item;
            } else {
                o.value = item.value;
                o.textContent = item.label;
            }
            if (o.value === current) {
                o.selected = true;
            }
            selectEl.appendChild(o);
        });
    }

    function refrescarFiltros() {
        return fetch(ENDPOINT, { credentials: "same-origin" })
            .then(function (resp) {
                if (!resp.ok) {
                    throw new Error("HTTP " + resp.status);
                }
                return resp.json();
            })
            .then(function (data) {
                fillSelect(document.querySelector('#filtroForm select[name="usuario"]'), data.usuarios || [], "Todos");
                fillSelect(document.querySelector('#filtroForm select[name="accion"]'), data.acciones || [], "Todas");
                fillSelect(document.querySelector('#filtroForm select[name="modulo"]'), data.modulos || [], "Todos");
            })
            .catch(function (err) {
                if (window.console) {
                    console.warn("[bitacora] no se pudieron cargar opciones de filtros:", err);
                }
            });
    }

    // Expone para que `lista.js` pueda invocarlo manualmente si lo necesita.
    window.BitacoraFiltros = {
        refrescar: refrescarFiltros,
    };
})();
