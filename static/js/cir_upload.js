document.addEventListener("DOMContentLoaded", function () {
  const uploadForm = document.getElementById("uploadForm");
  const spinner = document.getElementById("loadingSpinner"); // Asegurar que el spinner está presente

  if (!uploadForm || !spinner) return;

  uploadForm.addEventListener("submit", function (e) {
      e.preventDefault(); // Evita el envío tradicional
      spinner.style.display = "block"; // Muestra el spinner

      const formData = new FormData(uploadForm);

      fetch(uploadForm.action, {
          method: "POST",
          body: formData,
          headers: {
              "X-Requested-With": "XMLHttpRequest"
          }
      })
      .then(response => {
          if (!response.ok) {
              return response.json().then(data => { throw data; });
          }
          return response.json();
      })
      .then(data => {
          spinner.style.display = "none"; // Oculta el spinner

          if (data.success) {
              Swal.fire({
                  title: "Éxito",
                  text: data.message || "Archivos CIR cargados correctamente.",
                  icon: "success",
                  confirmButtonColor: "#3085d6",
                  confirmButtonText: "Aceptar"
              }).then(() => {
                  uploadForm.reset(); // Limpia el formulario después del éxito
                  document.getElementById('errorContainer').innerHTML = "";
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
      .catch(errorData => {
          spinner.style.display = "none";
          console.error('Error:', errorData);

          Swal.fire({
              title: "Error",
              text: errorData.error || "Error inesperado en la carga.",
              icon: "error",
              confirmButtonColor: "#d33",
              confirmButtonText: "Aceptar"
          });

          let errorHTML = '<div class="alert alert-danger" role="alert">';
          if (errorData.error_messages) {
              errorData.error_messages.forEach(msg => {
                  errorHTML += `<p>${msg}</p>`;
              });
          } else if (errorData.error) {
              errorHTML += `<p>${errorData.error}</p>`;
          }
          errorHTML += '</div>';
          document.getElementById('errorContainer').innerHTML = errorHTML;
      });
  });
});
