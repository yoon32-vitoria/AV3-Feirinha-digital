// ========================================================
// Script de Acessibilidade - FeirinhaDigital
// Permite alternar o Alto Contraste e o tamanho da fonte
// ========================================================

document.addEventListener("DOMContentLoaded", function () {
    const btnContraste = document.getElementById("btn-contraste");
    const btnAumentar = document.getElementById("btn-aumentar-fonte");
    const btnDiminuir = document.getElementById("btn-diminuir-fonte");

    // 1. Verifica se o usuário já havia ativado o Alto Contraste antes
    if (localStorage.getItem("altoContraste") === "ativo") {
        document.body.classList.add("alto-contraste");
        btnContraste.setAttribute("aria-pressed", "true");
    }

    // Alterna o modo de Alto Contraste ao clicar no botão
    btnContraste.addEventListener("click", function () {
        document.body.classList.toggle("alto-contraste");
        const ativo = document.body.classList.contains("alto-contraste");
        btnContraste.setAttribute("aria-pressed", ativo);
        localStorage.setItem("altoContraste", ativo ? "ativo" : "inativo");
    });

    // 2. Controle de tamanho da fonte (em porcentagem)
    let tamanhoFonte = parseInt(localStorage.getItem("tamanhoFonte")) || 100;
    document.documentElement.style.fontSize = tamanhoFonte + "%";

    btnAumentar.addEventListener("click", function () {
        if (tamanhoFonte < 130) {
            tamanhoFonte += 10;
            document.documentElement.style.fontSize = tamanhoFonte + "%";
            localStorage.setItem("tamanhoFonte", tamanhoFonte);
        }
    });

    btnDiminuir.addEventListener("click", function () {
        if (tamanhoFonte > 90) {
            tamanhoFonte -= 10;
            document.documentElement.style.fontSize = tamanhoFonte + "%";
            localStorage.setItem("tamanhoFonte", tamanhoFonte);
        }
    });
});
