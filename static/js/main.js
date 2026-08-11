document.addEventListener("DOMContentLoaded", function () {
    // Mobile nav toggle
    const toggle = document.getElementById("navToggle");
    const links = document.getElementById("navLinks");
    if (toggle && links) {
        toggle.addEventListener("click", function () {
            links.classList.toggle("open");
        });
    }

    // Live preview for profile picture upload ('+' icon)
    const picInput = document.querySelector('input[name="profile_pic"]');
    const picPreview = document.getElementById("picPreview");
    if (picInput && picPreview) {
        picInput.addEventListener("change", function () {
            const file = picInput.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function (e) {
                    picPreview.src = e.target.result;
                };
                reader.readAsDataURL(file);
            }
        });
    }

    // Auto-submit the profile picture form as soon as a file is chosen
    const autoSubmitInput = document.querySelector('input[data-autosubmit="true"]');
    if (autoSubmitInput) {
        autoSubmitInput.addEventListener("change", function () {
            if (autoSubmitInput.files.length > 0) {
                autoSubmitInput.closest("form").submit();
            }
        });
    }

    // Preview multiple room image uploads
    const roomImagesInput = document.getElementById("roomImagesInput");
    const roomImagesPreview = document.getElementById("roomImagesPreview");
    if (roomImagesInput && roomImagesPreview) {
        roomImagesInput.addEventListener("change", function () {
            roomImagesPreview.innerHTML = "";
            Array.from(roomImagesInput.files).forEach(function (file) {
                const reader = new FileReader();
                reader.onload = function (e) {
                    const img = document.createElement("img");
                    img.src = e.target.result;
                    img.style.height = "80px";
                    img.style.borderRadius = "6px";
                    img.style.marginRight = "8px";
                    img.style.display = "inline-block";
                    roomImagesPreview.appendChild(img);
                };
                reader.readAsDataURL(file);
            });
        });
    }

    // Auto-hide flash messages after a few seconds
    document.querySelectorAll(".flash").forEach(function (el) {
        setTimeout(function () {
            el.style.transition = "opacity 0.5s ease";
            el.style.opacity = "0";
            setTimeout(function () { el.remove(); }, 500);
        }, 4500);
    });
});
