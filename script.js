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
  } else {
    facilityRows.forEach((row) => row.classList.add("is-in-view"));
  }

  document.querySelector("#year").textContent = new Date().getFullYear();
});

