document.addEventListener("DOMContentLoaded", function () {
  // Dark Mode Toggle
  const darkToggle = document.getElementById('darkModeToggle');
  if (darkToggle) {
    darkToggle.addEventListener('click', () => {
      document.body.classList.toggle('dark-mode');
    });
  }

  // Contact Form Submission with Fetch
  const contactForm = document.getElementById("contactForm");
  if (contactForm) {
    contactForm.addEventListener("submit", async function (event) {
      event.preventDefault();

      const name = contactForm.querySelector('input[placeholder="Your Name"]').value.trim();
      const email = contactForm.querySelector('input[placeholder="Email Address"]').value.trim();
      const message = contactForm.querySelector('textarea').value.trim();

      if (!name || !email || !message) {
        alert("Please fill in all fields!");
        return;
      }

      try {
        const response = await fetch("http://127.0.0.1:5000/api/contact", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({ name, email, message })
        });

        const result = await response.json();

        if (response.ok) {
          alert(result.message);
          contactForm.reset();
        } else {
          alert("Error: " + result.message);
        }

      } catch (error) {
        console.error("Error submitting contact form:", error);
        alert("An error occurred. Please try again later.");
      }
    });
  }

  // Scroll Animation for Reveal
  const reveals = document.querySelectorAll('.reveal');
  window.addEventListener('scroll', () => {
    reveals.forEach((el) => {
      const top = el.getBoundingClientRect().top;
      if (top < window.innerHeight - 100) {
        el.classList.add('active');
      }
    });
  });

  // Sidebar Toggle
  const sidebarToggle = document.getElementById("sidebarToggle");
  if (sidebarToggle) {
    sidebarToggle.addEventListener("click", () => {
      toggleSidebar();
    });
  }
});

function toggleSidebar() {
  const sidebar = document.getElementById("sidebar");
  const overlay = document.getElementById("sidebarOverlay");
  if (sidebar && overlay) {
    sidebar.classList.toggle("active");
    overlay.classList.toggle("active");
  }
}
