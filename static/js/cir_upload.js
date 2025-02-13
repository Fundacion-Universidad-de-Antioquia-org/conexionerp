document.getElementById('uploadForm').addEventListener('submit', function(e) {
    e.preventDefault(); // Prevenir el envío normal del formulario

    const form = e.target;
    const formData = new FormData(form);
  
    fetch(form.action, {  // La URL viene del atributo action del form
      method: 'POST',
      body: formData,
      headers: {
        'X-Requested-With': 'XMLHttpRequest'
      }
    })
    .then(response => {
      if (!response.ok) {
        return response.json().then(data => { throw data; });
      }
      return response.json();
    })
    .then(data => {
      var successModal = new bootstrap.Modal(document.getElementById('successModal'));
      successModal.show();
      form.reset();
      document.getElementById('errorContainer').innerHTML = "";

      // **Limpia la URL del POST para evitar reenvíos en la recarga**
      window.history.replaceState(null, null, window.location.pathname);
    })
    .catch(errorData => {
      console.error('Error:', errorData);
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
