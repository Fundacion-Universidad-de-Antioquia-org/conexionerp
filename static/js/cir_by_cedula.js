document.addEventListener("DOMContentLoaded", function () {
    const filterCedula = document.getElementById("filterInput");
    const filterCompany = document.getElementById("companyFilter");
    const filterDateFrom = document.getElementById("startDate");
    const filterDateTo = document.getElementById("endDate");
    const resetFiltersBtn = document.getElementById("resetFilters");
    const tableRows = document.querySelectorAll("#certificatesTable tbody tr");

    if (!filterCedula || !filterCompany || !filterDateFrom || !filterDateTo || !resetFiltersBtn) {
        console.warn("Uno o más elementos de filtro no se encontraron en el DOM.");
        return;
    }

    function applyFilters() {
        let cedulaValue = filterCedula.value.toLowerCase();
        let companyValue = filterCompany.value.toLowerCase();
        let dateFromValue = filterDateFrom.value;
        let dateToValue = filterDateTo.value;

        tableRows.forEach(row => {
            let company = row.children[3].innerText.toLowerCase();
            let cedula = row.children[4].innerText.toLowerCase();
            let date = row.children[2].innerText; 

            let showRow = true;

            if (cedulaValue && !cedula.includes(cedulaValue)) showRow = false;
            if (companyValue && !company.includes(companyValue)) showRow = false;
            if (dateFromValue && date < dateFromValue) showRow = false;
            if (dateToValue && date > dateToValue) showRow = false;

            row.style.display = showRow ? "" : "none";
        });
    }
    function resetFilters() {
        filterCedula.value = "";
        filterCompany.value = "";
        filterDateFrom.value = "";
        filterDateTo.value = "";
        applyFilters();

        // Refrescar la página para cargar los datos completos
        window.location.href = window.location.pathname;
    }


    filterDateFrom.addEventListener("change", applyFilters);
    filterDateTo.addEventListener("change", applyFilters);
    resetFiltersBtn.addEventListener("click", resetFilters);
    // Seleccionar/Deseleccionar todos
    const selectAllCheckbox = document.getElementById("selectAll");
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener("change", function () {
            let checkboxes = document.querySelectorAll(".select-item");
            checkboxes.forEach(cb => cb.checked = this.checked);
        });
    }
});

// Obtener IDs seleccionados
function getSelectedIds() {
    let selected = [];
    document.querySelectorAll(".select-item:checked").forEach(cb => {
        selected.push(cb.value);
    });
    return selected;
}

// Descargar certificados seleccionados
function downloadFiltered() {
    let selectedIds = getSelectedIds();
    if (selectedIds.length === 0) {
        Swal.fire({
            title: "Advertencia",
            text: "No hay certificados seleccionados para descargar.",
            icon: "warning",
            confirmButtonColor: "#3085d6",
            confirmButtonText: "Aceptar"
        });
        return;
    }
    showLoading(); // Mostrar spinner

    let queryString = selectedIds.map(id => `ids=${id}`).join("&");
    window.location.href = `${downloadUrl}?${queryString}`;
    setTimeout(() => hideLoading(), 3000); // Ocultar después de 3 segundos

}

// Eliminar certificados con confirmación
function deleteFiltered() {
    let selectedIds = getSelectedIds();
    if (selectedIds.length === 0) {
        Swal.fire({
            title: "Advertencia",
            text: "No hay certificados seleccionados para eliminar.",
            icon: "warning",
            confirmButtonColor: "#3085d6",
            confirmButtonText: "Aceptar"
        });
        return;
    }

    Swal.fire({
        title: "¿Estás seguro?",
        text: "Esta acción eliminará los certificados seleccionados permanentemente.",
        icon: "warning",
        showCancelButton: true,
        confirmButtonColor: "#d33",
        cancelButtonColor: "#6c757d",
        confirmButtonText: "Sí, eliminar",
        cancelButtonText: "Cancelar"
    }).then((result) => {
        if (result.isConfirmed) {
            showLoading(); // Mostrar spinner

            fetch(deleteUrl, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCSRFToken()
                },
                body: JSON.stringify({ ids: selectedIds })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    selectedIds.forEach(id => {
                        let row = document.querySelector(`.select-item[value='${id}']`).closest("tr");
                        row.remove();
                    });
                    hideLoading(); // Ocultar spinner
                    Swal.fire({
                        title: "Eliminado",
                        text: "Los certificados han sido eliminados con éxito.",
                        icon: "success",
                        confirmButtonColor: "#28a745",
                        confirmButtonText: "Aceptar"
                    });
                } else {
                    hideLoading(); // Ocultar spinner
                    Swal.fire({
                        title: "Error",
                        text: "Error al eliminar certificados: " + (data.error || "Error desconocido."),
                        icon: "error",
                        confirmButtonColor: "#d33",
                        confirmButtonText: "Aceptar"
                    });
                }
            })
            .catch(error => {
                hideLoading(); // Ocultar spinner

                Swal.fire({
                    title: "Error",
                    text: "Hubo un problema con la eliminación.",
                    icon: "error",
                    confirmButtonColor: "#d33",
                    confirmButtonText: "Aceptar"
                });
            });
        }
    });
}
function showLoading() {
    document.getElementById("loadingSpinner").style.display = "flex";
}

function hideLoading() {
    document.getElementById("loadingSpinner").style.display = "none";
}
// Obtener el token CSRF de las cookies
function getCSRFToken() {
    let name = "csrftoken=";
    let decodedCookie = decodeURIComponent(document.cookie);
    let cookies = decodedCookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
        let cookie = cookies[i].trim();
        if (cookie.indexOf(name) === 0) {
            return cookie.substring(name.length, cookie.length);
        }
    }
    return "";
}
