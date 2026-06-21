document.addEventListener("DOMContentLoaded", function () {
  (function () {
    var form = document.getElementById("rolForm");
    var saveButton = document.getElementById("btnGuardarRol");

    if (!form || !saveButton) return;

    var controls = Array.prototype.slice
      .call(form.querySelectorAll("input, select, textarea"))
      .filter(function (control) {
        return control.name !== "csrfmiddlewaretoken";
      });

    var snapshot = function () {
      return controls
        .map(function (control) {
          if (control.type === "checkbox" || control.type === "radio") {
            return control.name + ":" + String(control.checked);
          }
          if (control.multiple) {
            return (
              control.name +
              ":" +
              Array.prototype.slice
                .call(control.selectedOptions)
                .map(function (option) {
                  return option.value;
                })
                .join(",")
            );
          }
          return control.name + ":" + String(control.value);
        })
        .join("|");
    };

    var initialState = snapshot();

    var toggleSave = function () {
      saveButton.disabled = snapshot() === initialState;
    };

    controls.forEach(function (control) {
      control.addEventListener("input", toggleSave);
      control.addEventListener("change", toggleSave);
    });

    form.addEventListener("submit", function () {
      saveButton.disabled = true;
      saveButton.innerHTML =
        '<i class="fa-solid fa-spinner fa-spin me-1"></i>Guardando';
    });
  })();
});
