document.addEventListener("DOMContentLoaded", function () {
  (function () {
    var form = document.getElementById("fotoPerfilForm");
    var uploadInput = document.getElementById("uploadPhotoInput");
    var cameraInput = document.getElementById("cameraPhotoInput");
    var deleteForm = document.getElementById("eliminarFotoForm");

    if (!form || !uploadInput || !cameraInput) return;

    Array.prototype.slice
      .call(document.querySelectorAll("[data-photo-action]"))
      .forEach(function (button) {
        button.addEventListener("click", function () {
          var action = button.getAttribute("data-photo-action");

          if (action === "upload") {
            uploadInput.click();
          }

          if (action === "camera") {
            cameraInput.click();
          }

          if (action === "delete" && deleteForm) {
            Swal.fire({
              title: "Quitar foto?",
              text: "Se eliminara la foto de tu perfil.",
              icon: "warning",
              showCancelButton: true,
              confirmButtonColor: "#dc3545",
              cancelButtonColor: "#6c757d",
              confirmButtonText: "Si, quitar",
              cancelButtonText: "Cancelar",
            }).then(function (result) {
              if (result.isConfirmed) {
                deleteForm.submit();
              }
            });
          }
        });
      });

    [uploadInput, cameraInput].forEach(function (input) {
      input.addEventListener("change", function () {
        if (input.files && input.files.length > 0) {
          form.submit();
        }
      });
    });
  })();
});
