window.addEventListener('DOMContentLoaded', function () {
    const toastElements = document.querySelectorAll(".toast");
    for (let toastElement of toastElements) {
        const toast = new bootstrap.Toast(toastElement);
        toast.show();
    }
});