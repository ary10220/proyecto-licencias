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

  function confirmarEliminacionCargo(button) {
    var url = button.getAttribute("data-url");
    var nombre = button.getAttribute("data-nombre");

    Swal.fire({
      title: "¿Eliminar cargo?",
      text: "Vas a eliminar el cargo " + nombre + ".",
      icon: "warning",
      showCancelButton: true,
      confirmButtonColor: "#dc3545",
      cancelButtonColor: "#6c757d",
      confirmButtonText: "Sí, eliminar",
      cancelButtonText: "Cancelar",
      preConfirm: function () {
        enviarPostSeguro(url);
        return new Promise(function () {});
      },
    });
  }

  window.enviarPostSeguro = enviarPostSeguro;
  window.confirmarEliminacionCargo = confirmarEliminacionCargo;
})();
