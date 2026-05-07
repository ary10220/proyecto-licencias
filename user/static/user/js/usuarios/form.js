document.addEventListener("DOMContentLoaded", function () {
  (function () {
    var form = document.getElementById("usuarioForm");
    var saveButton = document.getElementById("btnGuardarUsuario");

    if (!form || !saveButton) return;

    var controls = Array.prototype.slice
      .call(form.querySelectorAll("input, select, textarea"))
      .filter(function (control) {
        return (
          control.name &&
          control.name !== "csrfmiddlewaretoken" &&
          control.type !== "submit" &&
          control.type !== "button"
        );
      });

    var serializeControl = function (control) {
      if (control.type === "checkbox" || control.type === "radio") {
        return control.checked ? "1" : "0";
      }
      return control.value || "";
    };

    var snapshot = function () {
      return controls
        .map(function (control) {
          return [control.name, control.value, serializeControl(control)].join("::");
        })
        .sort()
        .join("||");
    };

    var initialSnapshot = snapshot();

    var syncSaveButton = function () {
      saveButton.disabled = snapshot() === initialSnapshot;
    };

    controls.forEach(function (control) {
      control.addEventListener("input", syncSaveButton);
      control.addEventListener("change", syncSaveButton);
    });

    syncSaveButton();

    form.addEventListener("submit", function () {
      saveButton.disabled = true;
      saveButton.innerHTML =
        '<i class="fa-solid fa-spinner fa-spin me-1"></i>Guardando';
    });
  })();

  (function () {
    var button = document.getElementById("btnResetPassword");
    if (!button) return;

    var url = button.getAttribute("data-reset-url");
    var csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (!url || !csrfInput) return;

    var inFlight = false;

    button.addEventListener("click", function () {
      var showConfirm = function (cb) {
        if (typeof Swal === "undefined") {
          if (
            confirm(
              "Se enviara un correo con un enlace de recuperacion al usuario. Continuar?"
            )
          )
            cb();
          return;
        }
        Swal.fire({
          title: "Restablecer contrase??a?",
          text: "Se enviara un correo con un enlace de recuperacion al usuario.",
          icon: "warning",
          showCancelButton: true,
          confirmButtonColor: "#df6e12",
          cancelButtonColor: "#6c757d",
          confirmButtonText: "Si, enviar",
          cancelButtonText: "Cancelar",
        }).then(function (result) {
          if (result.isConfirmed) cb();
        });
      };

      if (inFlight) return;

      showConfirm(function () {
        if (inFlight) return;
        inFlight = true;
        button.disabled = true;
        button.innerHTML =
          '<i class="fa-solid fa-spinner fa-spin me-1"></i>Enviando';

        var body = new FormData();
        body.append("csrfmiddlewaretoken", csrfInput.value);

        fetch(url, {
          method: "POST",
          headers: {
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": csrfInput.value,
          },
          body: body,
          credentials: "same-origin",
        })
          .then(function (res) {
            return res
              .json()
              .catch(function () {
                return {};
              })
              .then(function (data) {
                if (!res.ok || !data.ok) {
                  throw new Error(data.message || "No se pudo enviar el enlace.");
                }
                return data;
              });
          })
          .then(function (data) {
            if (typeof Swal === "undefined") {
              alert("Se envio el link de recuperacion a " + data.email + ".");
              return;
            }
            Swal.fire({
              title: "Enlace enviado",
              text: "Se envio el link de recuperacion a " + data.email + ".",
              icon: "success",
              confirmButtonColor: "#df6e12",
              confirmButtonText: "Confirmar",
            });
          })
          .catch(function (err) {
            if (typeof Swal === "undefined") {
              alert((err && err.message) || "No se pudo enviar el enlace.");
              return;
            }
            Swal.fire({
              title: "No se pudo enviar",
              text: (err && err.message) || "Intenta nuevamente.",
              icon: "error",
              confirmButtonColor: "#df6e12",
              confirmButtonText: "Entendido",
            });
          })
          .finally(function () {
            inFlight = false;
            button.disabled = false;
            button.innerHTML =
              '<i class="fa-solid fa-key me-1"></i>Restablecer contrasena';
          });
      });
    });
  })();
});
