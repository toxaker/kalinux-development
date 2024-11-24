document.addEventListener("DOMContentLoaded", () => {
  const navToggle = document.getElementById("nav-toggle");
  const navLinks = document.getElementById("nav-links");

  navToggle.addEventListener("click", () => {
    navLinks.classList.toggle("show");
  });

  const terminalInput = document.getElementById("terminal-input");
  const terminalOutput = document.getElementById("terminal-output");

  terminalInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      const command = terminalInput.value.trim();
      terminalOutput.innerHTML += `<p>$ ${command}</p>`;

      // Simulate bot response
      if (command === "help") {
        terminalOutput.innerHTML += "<p>Available commands: help, about, exit</p>";
      } else {
        terminalOutput.innerHTML += `<p>Unknown command: ${command}</p>`;
      }

      terminalInput.value = "";
      terminalOutput.scrollTop = terminalOutput.scrollHeight;
    }
  });
});
