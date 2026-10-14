// SLB Coliving PG — lightweight interactions, no extra libraries required.
document.addEventListener("DOMContentLoaded", () => {
  const menuButton = document.querySelector(".menu-toggle");
  const navigation = document.querySelector(".nav-links");

  // Responsive navigation closes after a visitor chooses a destination.
  menuButton.addEventListener("click", () => {
    const open = navigation.classList.toggle("open");
    menuButton.setAttribute("aria-expanded", String(open));
    menuButton.setAttribute(
      "aria-label",
      open ? "Close navigation" : "Open navigation",
    );
  });
  navigation.querySelectorAll("a").forEach((link) =>
    link.addEventListener("click", () => {
      navigation.classList.remove("open");
      menuButton.setAttribute("aria-expanded", "false");
      menuButton.setAttribute("aria-label", "Open navigation");
    }),
  );

  // Mark the visible page section in the navigation when supported.
  const navAnchors = [...document.querySelectorAll('.nav-links a[href^="#"]')];
  if ("IntersectionObserver" in window) {
    const sections = [...document.querySelectorAll("main section[id]")];
    const sectionObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            navAnchors.forEach((anchor) =>
              anchor.classList.toggle(
                "active",
                anchor.hash === `#${entry.target.id}`,
              ),
            );
          }
        });
      },
      { rootMargin: "-20% 0px -70% 0px" },
    );
    sections.forEach((section) => sectionObserver.observe(section));
  }

  // Reveal sections as they enter the viewport; keep them visible if unavailable.
  const revealElements = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window) {
    const revealObserver = new IntersectionObserver(
      (entries, observer) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.08 },
    );
    revealElements.forEach((element) => revealObserver.observe(element));
  } else {
    revealElements.forEach((element) => element.classList.add("is-visible"));
  }

  // Owner-supplied photo lightbox. Native dialog supports Escape to close.
  const lightbox = document.querySelector(".lightbox");
  const lightboxImage = lightbox.querySelector("img");
  document.querySelectorAll("[data-lightbox]").forEach((button) =>
    button.addEventListener("click", () => {
      lightboxImage.src = button.dataset.lightbox;
      lightboxImage.alt =
        button.dataset.lightboxAlt || "Owner-supplied PG photo";
      lightbox.showModal();
    }),
  );
  lightbox
    .querySelector(".lightbox-close")
    .addEventListener("click", () => lightbox.close());
  lightbox.addEventListener("click", (event) => {
    if (event.target === lightbox) lightbox.close();
  });

  // Booking form checks. The draft link is user-triggered; this static page never
  // sends or stores the visitor's details itself.
  const form = document.querySelector("#booking-form");
  const message = document.querySelector(".form-message");
  const dateInput = form.elements.date;
  const localDate = () =>
    new Date(Date.now() - new Date().getTimezoneOffset() * 60000)
      .toISOString()
      .slice(0, 10);
  dateInput.min = localDate();

  const showFieldError = (field, text) => {
    const error = field.closest("label").querySelector(".field-error");
    if (error) error.textContent = text;
    field.setAttribute("aria-invalid", text ? "true" : "false");
  };
  form
    .querySelectorAll("input,select,textarea")
    .forEach((field) =>
      field.addEventListener("input", () => showFieldError(field, "")),
    );

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    message.hidden = true;
    message.classList.remove("error");
    form.querySelectorAll(".field-error").forEach((error) => {
      error.textContent = "";
    });
    form
      .querySelectorAll('[aria-invalid="true"]')
      .forEach((field) => field.removeAttribute("aria-invalid"));

    const name = form.elements.name.value.trim();
    const rawPhone = form.elements.phone.value.trim();
    const phone = rawPhone.replace(/[\s()-]/g, "");
    const date = form.elements.date.value;
    const room = form.elements.room.value;
    let valid = true;
    const fail = (field, text) => {
      showFieldError(field, text);
      valid = false;
    };

    if (name.length < 2)
      fail(form.elements.name, "Enter your full name (at least 2 characters).");
    if (!/^\+?[0-9]{10,15}$/.test(phone))
      fail(
        form.elements.phone,
        "Enter a valid phone number with 10–15 digits.",
      );
    if (!room)
      fail(
        form.elements.room,
        "Choose a room preference or select “Other / not sure”.",
      );
    if (!date || date < localDate())
      fail(form.elements.date, "Choose today or a future move-in date.");
    if (!valid) {
      message.textContent =
        "Please review the highlighted fields and try again.";
      message.classList.add("error");
      message.hidden = false;
      form.querySelector('[aria-invalid="true"]')?.focus();
      return;
    }

    const requirements =
      form.elements.requirements.value.trim() || "None added";
    const callTime = form.elements.callTime?.value || "ASAP";
    const draft = `Hello, I would like to enquire about SLB Coliving PG. Name: ${name}. Phone: ${rawPhone}. Room preference: ${room}. Check-in date: ${date}. Best time to call: ${callTime}. Special requirements: ${requirements}.`;
    const whatsappUrl = `https://wa.me/919966367235?text=${encodeURIComponent(draft)}`;

    const submitBtn = form.querySelector("#submit-btn");
    const originalBtnText = submitBtn ? submitBtn.innerHTML : "Request Call-Back";
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = "Submitting request... ⏳";
    }

    const API_BASE = window.location.origin.includes("http") ? window.location.origin : "http://localhost:8000";

    // Submit lead to FastAPI Backend
    fetch(`${API_BASE}/api/leads`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        fullName: name,
        phone: phone,
        roomType: room,
        moveInDate: date,
        preferredCallTime: callTime,
        requirements: requirements !== "None added" ? requirements : null,
      }),
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error("Backend response error");
        }
        return response.json();
      })
      .then((savedLead) => {
        message.replaceChildren();
        const successBox = document.createElement("div");
        successBox.style.padding = "0.75rem 0";

        const title = document.createElement("strong");
        title.style.display = "block";
        title.style.color = "#10b981";
        title.style.fontSize = "1.05rem";
        title.style.marginBottom = "0.4rem";
        title.textContent = "✓ Call-Back Request Received!";

        const copy = document.createElement("p");
        copy.textContent = `Thanks, ${name}! Your request for ${room} has been recorded in our system. Our PG team will call you back at ${rawPhone} (${callTime}).`;

        const waPrompt = document.createElement("p");
        waPrompt.style.marginTop = "0.5rem";
        waPrompt.style.fontSize = "0.85rem";
        waPrompt.style.color = "var(--text-muted, #aaa)";
        waPrompt.textContent = "Need an immediate answer right now?";

        const sendLink = document.createElement("a");
        sendLink.href = whatsappUrl;
        sendLink.target = "_blank";
        sendLink.rel = "noopener";
        sendLink.className = "button";
        sendLink.style.marginTop = "0.5rem";
        sendLink.style.display = "inline-flex";
        sendLink.textContent = "Chat on WhatsApp now ↗";

        successBox.append(title, copy, waPrompt, sendLink);
        message.append(successBox);
        message.hidden = false;
        form.reset();
        dateInput.min = localDate();
      })
      .catch((err) => {
        // Graceful fallback if backend is offline or on purely static file:// host
        console.warn("FastAPI backend offline or unreachable, providing WhatsApp fallback:", err);
        message.replaceChildren();
        const copy = document.createElement("p");
        copy.textContent = `Thanks, ${name}. Your call-back request is prepared. Tap WhatsApp below to send your details directly to the manager, or call us directly.`;
        const sendLink = document.createElement("a");
        sendLink.href = whatsappUrl;
        sendLink.target = "_blank";
        sendLink.rel = "noopener";
        sendLink.textContent = "Send via WhatsApp ↗";
        message.append(copy, sendLink);
        message.hidden = false;
      })
      .finally(() => {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerHTML = originalBtnText;
        }
      });
  });

  // Facility marquee: clicking a name pauses its row and reveals only its
  // existing category description. Mouse departure or close resumes motion.
  const facilityRows = [...document.querySelectorAll("[data-facility-row]")];
  let activeFacilityRow = null;
  let activeFacilityButton = null;
  let activeFacilityName = null;

  const closeFacilityDetail = (restoreFocus = false) => {
    if (!activeFacilityRow) return;
    const row = activeFacilityRow;
    const detail = row.querySelector(".facility-detail");
    const focusTarget = activeFacilityButton;
    const focusWasInDetail = detail?.contains(document.activeElement) ?? false;

    row.classList.remove("is-selected");
    row.querySelectorAll(".facility-marquee-item").forEach((item) => {
      item.classList.remove("is-active-name");
    });
    row.querySelectorAll("button.facility-marquee-item").forEach((button) => {
      button.setAttribute("aria-pressed", "false");
    });
    if (detail) {
      detail.hidden = true;
      detail.querySelector(".facility-detail-category").textContent = "";
      detail.querySelector(".facility-detail-name").textContent = "";
      detail.querySelector(".facility-detail-description").textContent = "";
    }
    activeFacilityRow = null;
    activeFacilityButton = null;
    activeFacilityName = null;

    if (restoreFocus || focusWasInDetail) {
      focusTarget?.focus({ preventScroll: true });
    }
  };

  facilityRows.forEach((row) => {
    const detail = row.querySelector(".facility-detail");

    row.addEventListener("click", (event) => {
      const close = event.target.closest(".facility-detail-close");
      if (close) {
        closeFacilityDetail(true);
        return;
      }

      const item = event.target.closest(".facility-marquee-item");
      if (!item || !row.contains(item)) return;
      const name = item.dataset.facilityName;

      if (
        activeFacilityRow === row &&
        activeFacilityName === name
      ) {
        closeFacilityDetail(true);
        return;
      }

      closeFacilityDetail();
      activeFacilityRow = row;
      activeFacilityName = name;
      activeFacilityButton =
        item.tagName === "BUTTON"
          ? item
          : document.activeElement instanceof HTMLElement &&
              document.activeElement !== document.body
            ? document.activeElement
            : null;
      row.classList.add("is-selected");
      row.querySelectorAll(".facility-marquee-item").forEach((candidate) => {
        candidate.classList.toggle(
          "is-active-name",
          candidate.dataset.facilityName === name,
        );
      });
      row.querySelectorAll("button.facility-marquee-item").forEach((candidate) => {
        candidate.setAttribute(
          "aria-pressed",
          String(candidate.dataset.facilityName === name),
        );
      });
      detail.querySelector(".facility-detail-category").textContent =
        item.dataset.categoryTitle;
      detail.querySelector(".facility-detail-name").textContent = name;
      detail.querySelector(".facility-detail-description").textContent =
        item.dataset.categoryDescription;
      detail.hidden = false;
    });

    row.addEventListener("pointerleave", (event) => {
      if (event.pointerType !== "mouse" || activeFacilityRow !== row) return;
      if (event.relatedTarget && row.contains(event.relatedTarget)) return;
      closeFacilityDetail(false);
    });

    row.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && activeFacilityRow === row) {
        closeFacilityDetail(true);
      }
    });

    row.addEventListener("focusout", (event) => {
      if (activeFacilityRow !== row) return;
      if (event.relatedTarget && row.contains(event.relatedTarget)) return;
      closeFacilityDetail(false);
    });
  });

  if ("IntersectionObserver" in window) {
    const facilityObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          entry.target.classList.toggle("is-in-view", entry.isIntersecting);
          if (!entry.isIntersecting && activeFacilityRow === entry.target) {
            closeFacilityDetail();
          }
        });
      },
      { rootMargin: "80px 0px", threshold: 0.01 },
    );
    facilityRows.forEach((row) => facilityObserver.observe(row));

    const facilitiesSection = document.querySelector("#facilities");
    const sectionButterflyObserver = new IntersectionObserver(
      ([entry]) => {
        document.body.classList.toggle(
          "facilities-marquee-active",
          entry.isIntersecting,
        );
      },
      { threshold: 0.01 },
    );
    if (facilitiesSection) sectionButterflyObserver.observe(facilitiesSection);
  } else {
    facilityRows.forEach((row) => row.classList.add("is-in-view"));
  }

  document.querySelector("#year").textContent = new Date().getFullYear();
});


// Lightweight SVG butterflies: a staggered entrance flight plus sparse ambient passes.
(() => {
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  if (reducedMotion.matches || !document.body) return;

  const svgNamespace = "http://www.w3.org/2000/svg";
  const layer = document.createElement("div");
  layer.className = "butterfly-flight-layer";
  layer.setAttribute("aria-hidden", "true");
  document.body.appendChild(layer);

  const palette = [
    { wing: "#9b1739", light: "#ed9aad", detail: "#6d1730", glow: "#b93658" },
    { wing: "#cb5870", light: "#ffe0e5", detail: "#96344e", glow: "#e78ca0" },
    { wing: "#dfcbae", light: "#fff6e8", detail: "#a98766", glow: "#e4d4bd" },
    { wing: "#f0e6de", light: "#f4b5c2", detail: "#b36377", glow: "#f3cad2" },
    { wing: "#70243d", light: "#e8a8b5", detail: "#4a192c", glow: "#a03e5b" },
    { wing: "#d9b9a8", light: "#fff2e8", detail: "#a96769", glow: "#e9b8aa" },
  ];

  const artwork = `
    <g class="svg-butterfly-wing svg-butterfly-wing--left">
      <path class="butterfly-upper" d="M31 23C25 15 18 5 9 5 2 6 3 17 7 22c5 6 15 5 24 2Z"/>
      <path class="butterfly-lower" d="M31 25c-8 2-15 6-16 13-1 6 6 8 11 3 3-3 4-10 5-16Z"/>
      <path class="butterfly-vein" d="M30 23C23 18 17 12 9 8m20 17c-6 2-10 6-12 11"/>
      <circle class="butterfly-spot" cx="10" cy="14" r="1.5"/><circle class="butterfly-spot" cx="20" cy="35" r="1.1"/>
    </g>
    <g class="svg-butterfly-wing svg-butterfly-wing--right">
      <path class="butterfly-upper" d="M33 23c6-8 13-18 22-18 7 1 6 12 2 17-5 6-15 5-24 2Z"/>
      <path class="butterfly-lower" d="M33 25c8 2 15 6 16 13 1 6-6 8-11 3-3-3-4-10-5-16Z"/>
      <path class="butterfly-vein" d="M34 23c7-5 13-11 21-15m-20 17c6 2 10 6 12 11"/>
      <circle class="butterfly-spot" cx="54" cy="14" r="1.5"/><circle class="butterfly-spot" cx="44" cy="35" r="1.1"/>
    </g>
    <path class="svg-butterfly-body" d="M31.3 19c-2 4-2 11 .7 16 2.7-5 2.7-12 .7-16Z"/>
    <path class="svg-butterfly-antennae" d="M31.7 20c-1.1-4-3.4-6.6-6.5-8m7.1 8c1.1-4 3.4-6.6 6.5-8"/>
  `;

  const makeButterfly = ({ top, rise, dip, delay, duration, color, size, ambient = false }) => {
    const butterfly = document.createElement("span");
    butterfly.className = `butterfly-flight${ambient ? " butterfly-flight--ambient" : ""}`;
    const tones = palette[color % palette.length];
    butterfly.style.setProperty("--start-y", top);
    butterfly.style.setProperty("--rise", rise);
    butterfly.style.setProperty("--dip", dip);
    butterfly.style.setProperty("--flight-delay", delay);
    butterfly.style.setProperty("--flight-time", duration);
    butterfly.style.setProperty("--butterfly-size", size);
    butterfly.style.setProperty("--butterfly-height", `${Number.parseFloat(size) * .75}px`);
    butterfly.style.setProperty("--wing", tones.wing);
    butterfly.style.setProperty("--wing-light", tones.light);
    butterfly.style.setProperty("--wing-detail", tones.detail);
    butterfly.style.setProperty("--butterfly-glow", tones.glow);

    const svg = document.createElementNS(svgNamespace, "svg");
    svg.setAttribute("viewBox", "0 0 64 48");
    svg.setAttribute("aria-hidden", "true");
    svg.setAttribute("focusable", "false");
    svg.classList.add("butterfly-svg");
    svg.innerHTML = artwork;
    butterfly.appendChild(svg);
    butterfly.addEventListener("animationend", (event) => {
      if (event.target === butterfly) butterfly.remove();
    });
    layer.appendChild(butterfly);
  };

  [
    { top: "10%", rise: "-2.8vh", dip: "2vh", delay: "0ms", duration: "10.2s", color: 0, size: "48px" },
    { top: "24%", rise: "2.4vh", dip: "-3vh", delay: "420ms", duration: "11.4s", color: 1, size: "40px" },
    { top: "39%", rise: "-3.4vh", dip: "2.2vh", delay: "840ms", duration: "9.7s", color: 2, size: "54px" },
    { top: "56%", rise: "2.8vh", dip: "-2.4vh", delay: "1260ms", duration: "12.1s", color: 3, size: "38px" },
    { top: "72%", rise: "-2.4vh", dip: "3vh", delay: "1680ms", duration: "10.8s", color: 4, size: "46px" },
    { top: "86%", rise: "2vh", dip: "-2.6vh", delay: "2100ms", duration: "11.7s", color: 5, size: "36px" },
  ].forEach((flight) => makeButterfly(flight));

  let ambientTimer;
  const scheduleAmbient = () => {
    const wait = 6500 + Math.random() * 6000;
    ambientTimer = window.setTimeout(() => {
      if (!document.hidden && !reducedMotion.matches && layer.isConnected) {
        const active = layer.querySelectorAll(".butterfly-flight--ambient").length;
        if (active < 2) {
          const rise = 1.5 + Math.random() * 3;
          const dip = 1.5 + Math.random() * 3;
          makeButterfly({
            top: `${14 + Math.random() * 70}%`,
            rise: `${Math.random() < .5 ? "-" : ""}${rise.toFixed(1)}vh`,
            dip: `${Math.random() < .5 ? "-" : ""}${dip.toFixed(1)}vh`,
            delay: "0ms",
            duration: `${12 + Math.random() * 4}s`,
            color: Math.floor(Math.random() * palette.length),
            size: `${34 + Math.random() * 17}px`,
            ambient: true,
          });
        }
      }
      scheduleAmbient();
    }, wait);
  };
  scheduleAmbient();

  const stopForReducedMotion = (event) => {
    if (!event.matches) return;
    window.clearTimeout(ambientTimer);
    layer.remove();
  };
  if (typeof reducedMotion.addEventListener === "function") {
    reducedMotion.addEventListener("change", stopForReducedMotion);
  } else if (typeof reducedMotion.addListener === "function") {
    reducedMotion.addListener(stopForReducedMotion);
  }
})();
