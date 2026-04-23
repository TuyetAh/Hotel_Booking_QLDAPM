//điều khiển dropdown và slider
document.addEventListener("DOMContentLoaded", function () {
    // =========================
    // 1. Bộ chọn người lớn / phòng
    // =========================
    const guestRoomDisplay = document.getElementById("guestRoomDisplay");
    const guestRoomDropdown = document.getElementById("guestRoomDropdown");
    const guestRoomDone = document.getElementById("guestRoomDone");
    const guestRoomSummary = document.getElementById("guestRoomSummary");
    const guestRoomArrow = document.getElementById("guestRoomArrow");

    const adultMinus = document.getElementById("adultMinus");
    const adultPlus = document.getElementById("adultPlus");
    const roomMinus = document.getElementById("roomMinus");
    const roomPlus = document.getElementById("roomPlus");

    const adultCount = document.getElementById("adultCount");
    const roomCount = document.getElementById("roomCount");

    const adultInput = document.getElementById("adultInput");
    const roomInput = document.getElementById("roomInput");

    let adults = parseInt(adultInput?.value || "2");
    let rooms = parseInt(roomInput?.value || "1");

    function updateGuestRoomSummary() {
        if (guestRoomSummary) {
            guestRoomSummary.textContent = `${adults} người lớn, ${rooms} phòng`;
        }

        if (adultCount) adultCount.textContent = adults;
        if (roomCount) roomCount.textContent = rooms;

        if (adultInput) adultInput.value = adults;
        if (roomInput) roomInput.value = rooms;

        if (adultMinus) adultMinus.disabled = adults <= 1;
        if (roomMinus) roomMinus.disabled = rooms <= 1;
    }

    function toggleGuestDropdown(show) {
        if (!guestRoomDropdown || !guestRoomArrow) return;

        if (show) {
            guestRoomDropdown.classList.add("show");
            guestRoomArrow.classList.remove("fa-angle-up");
            guestRoomArrow.classList.add("fa-angle-down");
        } else {
            guestRoomDropdown.classList.remove("show");
            guestRoomArrow.classList.remove("fa-angle-down");
            guestRoomArrow.classList.add("fa-angle-up");
        }
    }

    if (guestRoomDisplay) {
        guestRoomDisplay.addEventListener("click", function (e) {
            e.stopPropagation();
            const isOpen = guestRoomDropdown.classList.contains("show");
            toggleGuestDropdown(!isOpen);
        });
    }

    if (guestRoomDone) {
        guestRoomDone.addEventListener("click", function () {
            toggleGuestDropdown(false);
        });
    }

    if (adultPlus) {
        adultPlus.addEventListener("click", function () {
            adults++;
            updateGuestRoomSummary();
        });
    }

    if (adultMinus) {
        adultMinus.addEventListener("click", function () {
            if (adults > 1) adults--;
            updateGuestRoomSummary();
        });
    }

    if (roomPlus) {
        roomPlus.addEventListener("click", function () {
            rooms++;
            updateGuestRoomSummary();
        });
    }

    if (roomMinus) {
        roomMinus.addEventListener("click", function () {
            if (rooms > 1) rooms--;
            updateGuestRoomSummary();
        });
    }

    document.addEventListener("click", function (e) {
        if (
            guestRoomDropdown &&
            guestRoomDisplay &&
            !guestRoomDropdown.contains(e.target) &&
            !guestRoomDisplay.contains(e.target)
        ) {
            toggleGuestDropdown(false);
        }
    });

    updateGuestRoomSummary();

    // =========================
    // 2. Slider khách sạn nổi bật
    // =========================
    const track = document.getElementById("featuredSliderTrack");
    const prevBtn = document.getElementById("featuredPrev");
    const nextBtn = document.getElementById("featuredNext");

    if (track && prevBtn && nextBtn) {
        const slides = track.querySelectorAll(".featured-slide");
        let currentIndex = 0;

        function getVisibleCount() {
            if (window.innerWidth <= 768) return 1;
            if (window.innerWidth <= 1100) return 2;
            return 4;
        }

        function updateSlider() {
            const visibleCount = getVisibleCount();
            const totalSlides = slides.length;

            if (totalSlides === 0) {
                prevBtn.disabled = true;
                nextBtn.disabled = true;
                return;
            }

            const slideWidth = slides[0].offsetWidth;
            const gap = 18;
            const offset = currentIndex * (slideWidth + gap);

            track.style.transform = `translateX(-${offset}px)`;

            prevBtn.disabled = currentIndex <= 0;
            nextBtn.disabled = currentIndex >= totalSlides - visibleCount;
        }

        nextBtn.addEventListener("click", function () {
            const visibleCount = getVisibleCount();
            const totalSlides = slides.length;

            if (currentIndex < totalSlides - visibleCount) {
                currentIndex++;
                updateSlider();
            }
        });

        prevBtn.addEventListener("click", function () {
            if (currentIndex > 0) {
                currentIndex--;
                updateSlider();
            }
        });

        window.addEventListener("resize", function () {
            const visibleCount = getVisibleCount();
            const totalSlides = slides.length;

            if (currentIndex > totalSlides - visibleCount) {
                currentIndex = Math.max(0, totalSlides - visibleCount);
            }

            updateSlider();
        });

        updateSlider();
    }
});

// =========================
// 3. Auto submit bộ lọc trang tìm kiếm
// =========================
document.addEventListener("DOMContentLoaded", function () {
    const autoFilterForm = document.getElementById("autoFilterForm");
    if (!autoFilterForm) return;

    const changeInputs = autoFilterForm.querySelectorAll(".auto-submit-change");
    const textInputs = autoFilterForm.querySelectorAll(".auto-submit-input");

    let debounceTimer = null;

    changeInputs.forEach((input) => {
        input.addEventListener("change", function () {
            autoFilterForm.submit();
        });
    });

    textInputs.forEach((input) => {
        input.addEventListener("input", function () {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                autoFilterForm.submit();
            }, 600);
        });
    });
});


// =========================
// 4. Radio có thể click lại để bỏ chọn
// =========================
document.addEventListener("DOMContentLoaded", function () {
    const radios = document.querySelectorAll(".auto-submit-change[type='radio']");

    radios.forEach((radio) => {
        // lưu trạng thái trước đó
        radio.dataset.checked = radio.checked;

        radio.addEventListener("click", function (e) {
            // nếu đã chọn rồi thì bỏ chọn
            if (this.dataset.checked === "true") {
                this.checked = false;
                this.dataset.checked = "false";

                // submit lại form
                const form = document.getElementById("autoFilterForm");
                if (form) form.submit();

                e.preventDefault(); // chặn hành vi mặc định
            } else {
                // reset tất cả radio cùng name
                document.querySelectorAll(`input[name="${this.name}"]`).forEach(r => {
                    r.dataset.checked = "false";
                });

                this.dataset.checked = "true";
            }
        });

        // cập nhật trạng thái khi change (quan trọng)
        radio.addEventListener("change", function () {
            document.querySelectorAll(`input[name="${this.name}"]`).forEach(r => {
                r.dataset.checked = "false";
            });

            this.dataset.checked = "true";
        });
    });
});