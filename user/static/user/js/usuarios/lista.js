(function () {
  function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      var cookies = document.cookie.split(";");
      for (var i = 0; i < cookies.length; i++) {
        var cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === name + "=") {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  function enviarPostSeguro(url) {
    var form = document.createElement("form");
    form.method = "POST";
    form.action = url;

    var csrf = document.createElement("input");
    csrf.type = "hidden";
    csrf.name = "csrfmiddlewaretoken";
    csrf.value = getCookie("csrftoken") || "";

    form.appendChild(csrf);
    document.body.appendChild(form);
    form.submit();
  }

  function confirmarToggleUsuario(button) {
    var url = button.getAttribute("data-url");
    var nombre = button.getAttribute("data-nombre");
    var activo = button.getAttribute("data-activo") === "1";
    var accion = activo ? "desactivar" : "activar";

    Swal.fire({
      title: activo ? "¿Desactivar usuario?" : "¿Activar usuario?",
      text: "Vas a " + accion + " el usuario " + nombre + ".",
      icon: "warning",
      showCancelButton: true,
      confirmButtonColor: activo ? "#dc3545" : "#198754",
      cancelButtonColor: "#6c757d",
      confirmButtonText: "Sí, " + accion,
      cancelButtonText: "Cancelar",
      preConfirm: function () {
        enviarPostSeguro(url);
        return new Promise(function () {});
      },
    });
  }

  // These functions are referenced from inline onclick handlers in the template.
  window.enviarPostSeguro = enviarPostSeguro;
  window.confirmarToggleUsuario = confirmarToggleUsuario;
})();
