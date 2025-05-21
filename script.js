document.addEventListener("DOMContentLoaded", function () {
    const textElement = document.querySelector(".hero-content h2");
    const fullText = "Hi, I'm CEH Certified - Siddhesh Shinde";
    let index = 0;

    function typeText() {
        if (index <= fullText.length) {
            const typedText = fullText.substring(0, index);
            const highlighted = typedText.replace(
                "CEH Certified - Siddhesh Shinde",
                `<span>CEH Certified - Siddhesh Shinde</span>`
            );
            textElement.innerHTML = highlighted;
            index++;
            setTimeout(typeText, 100);
        }
    }

    typeText();
});
