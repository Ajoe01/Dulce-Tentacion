// script.js

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".card").forEach(card => {
        const input = card.querySelector(".cantidad-input");

        // Botones + y -
        const btnMas = card.querySelector(".mas");
        const btnMenos = card.querySelector(".menos");

        if (btnMas && btnMenos) {
            btnMas.addEventListener("click", () => input.value = parseInt(input.value) + 1);
            btnMenos.addEventListener("click", () => {
                if (parseInt(input.value) > 1) input.value = parseInt(input.value) - 1;
            });
        }

        // Botón agregar al carrito
        const btnAgregar = card.querySelector(".agregar-btn");
        if (btnAgregar) {
            btnAgregar.addEventListener("click", () => {
                const nombre = card.querySelector("h3").textContent;

                let precio = 0;
                let opcion = "N/A";

                // Si hay select de opciones
                const selectOpc = card.querySelector(".opcion");
                if (selectOpc) {
                    precio = parseInt(selectOpc.value);
                    opcion = selectOpc.selectedOptions[0].textContent;
                } else {
                    // Tomar precio del <p class="precio">
                    const pPrecio = card.querySelector("p.precio");
                    if (pPrecio) precio = parseInt(pPrecio.textContent.trim());
                }

                const cantidad = parseInt(input.value);

                // Guardar en localStorage
                let carrito = JSON.parse(localStorage.getItem("carrito")) || [];
                carrito.push({ nombre, opcion, precio, cantidad });
                localStorage.setItem("carrito", JSON.stringify(carrito));

                alert(`${nombre} agregado al carrito ✅`);
            });
        }
    });
});
