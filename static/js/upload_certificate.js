document.addEventListener("DOMContentLoaded", function () {
  const uploadForm = document.getElementById("uploadForm");
  const spinner = document.getElementById("loadingSpinner"); // Usar el de base.html

  if (!uploadForm || !spinner) return;

  uploadForm.addEventListener("submit", function (event) {
      event.preventDefault(); // Evita recargar la página
      spinner.style.display = "block"; // Muestra el spinner global

      let formData = new FormData(uploadForm);

      fetch(uploadForm.action, {
          method: "POST",
          body: formData,
          headers: {
              "X-Requested-With": "XMLHttpRequest"
          }
      })
      .then(response => response.json())
      .then(data => {
          spinner.style.display = "none"; // Ocultar el spinner global

          if (data.success) {
              Swal.fire({
                  title: "Éxito",
                  text: data.message || "Certificados cargados correctamente.",
                  icon: "success",
                  confirmButtonColor: "#3085d6",
                  confirmButtonText: "Aceptar"
              }).then(() => {
                  uploadForm.reset(); // Resetear formulario después del éxito
              });
          } else {
              Swal.fire({
                  title: "Error",
                  text: data.error || "Hubo un problema en la carga.",
                  icon: "error",
                  confirmButtonColor: "#d33",
                  confirmButtonText: "Aceptar"
              });
          }
      })
      .catch(error => {
          spinner.style.display = "none";
          console.error("Error en la carga:", error);
          Swal.fire({
              title: "Error",
              text: "Error inesperado en la carga.",
              icon: "error",
              confirmButtonColor: "#d33",
              confirmButtonText: "Aceptar"
          });
      });
  });
});
