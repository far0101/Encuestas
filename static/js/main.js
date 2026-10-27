// static/js/main.js
// Logica general de la interfaz

document.addEventListener("DOMContentLoaded", function () {

    // Auto-cerrar alertas flash despues de 4 segundos
    const alertas = document.querySelectorAll(".flash-auto");
    alertas.forEach(function (alerta) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alerta);
            bsAlert.close();
        }, 4000);
    });

    // Confirmacion de eliminacion con modal
    const botonesEliminar = document.querySelectorAll("[data-confirm]");
    botonesEliminar.forEach(function (btn) {
        btn.addEventListener("click", function (e) {
            e.preventDefault();
            const mensaje = btn.getAttribute("data-confirm");
            const form = btn.closest("form");

            document.getElementById("modalConfirmMensaje").textContent = mensaje;
            const modal = new bootstrap.Modal(document.getElementById("modalConfirm"));

            document.getElementById("btnConfirmarEliminar").onclick = function () {
                form.submit();
            };

            modal.show();
        });
    });

});

