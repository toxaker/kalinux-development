document.addEventListener("DOMContentLoaded", () => {
    /**
     * Display a loading spinner
     */
    function displayLoader(elementId) {
        document.getElementById(elementId).innerHTML = `<div class="loading">Loading...</div>`;
    }

    /**
     * Display error messages
     */
    function displayError(errorMessage, elementId) {
        document.getElementById(elementId).innerHTML = `<div class="error">Error: ${errorMessage}</div>`;
    }

    /**
     * Handle API form submission
     */
    function handleFormSubmit(formId, endpoint, resultId, renderFunction) {
        document.getElementById(formId).addEventListener("submit", async (e) => {
            e.preventDefault();

            const formData = new FormData(document.getElementById(formId));
            const payload = Object.fromEntries(formData.entries());

            displayLoader(resultId);

            try {
                const response = await fetch(endpoint, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload),
                });

                if (!response.ok) throw new Error(await response.text());
                const data = await response.json();

                if (data.success) {
                    renderFunction(data.data, resultId);
                } else {
                    displayError(data.error, resultId);
                }
            } catch (error) {
                displayError(error.message, resultId);
            }
        });
    }

    /**
     * Render functions
     */
    const renderIpInfo = (data, resultId) => {
        document.getElementById(resultId).innerHTML = `
            <h3>IP Info:</h3>
            <p><strong>IP:</strong> ${data.ip}</p>
            <p><strong>City:</strong> ${data.city || "N/A"}</p>
            <p><strong>Region:</strong> ${data.region || "N/A"}</p>
            <p><strong>Country:</strong> ${data.country || "N/A"}</p>
            <p><strong>ISP:</strong> ${data.org || "N/A"}</p>`;
    };

    const renderDnsInfo = (data, resultId) => {
        document.getElementById(resultId).innerHTML = `
            <h3>DNS Records:</h3>
            <ul>${data.dns_records.map(record => `<li>${record}</li>`).join("")}</ul>`;
    };

    const renderReverseDnsInfo = (data, resultId) => {
        document.getElementById(resultId).innerHTML = `
            <h3>Reverse DNS:</h3>
            <p>${data.reverse_dns}</p>`;
    };

    const renderScanResult = (data, resultId) => {
        document.getElementById(resultId).innerHTML = `
            <h3>Open Ports:</h3>
            <p>${data.open_ports.join(", ")}</p>`;
    };

    /**
     * Bind forms to their respective API endpoints
     */
    handleFormSubmit("portScannerForm", "/scan_ports", "scanResult", renderScanResult);
    handleFormSubmit("ipForm", "/get_ip_info", "ipInfoResult", renderIpInfo);
    handleFormSubmit("dnsLookupForm", "/dns_lookup", "dnsInfo", renderDnsInfo);
    handleFormSubmit("reverseDnsForm", "/reverse_dns_lookup", "reverseDnsInfo", renderReverseDnsInfo);
});

document.addEventListener("DOMContentLoaded", () => {
    // Real-time system metrics
    const socket = io.connect("http://localhost:5000");

    socket.on("system_metrics", (data) => {
        document.getElementById("cpuUsage").innerText = `${data.cpu_usage}%`;
        document.getElementById("memoryUsage").innerText = `${data.memory_usage}%`;
        document.getElementById("diskUsage").innerText = `${data.disk_usage}%`;
        document.getElementById("bytesSent").innerText = `${(data.network.bytes_sent / 1024).toFixed(2)} KB`;
        document.getElementById("bytesReceived").innerText = `${(data.network.bytes_received / 1024).toFixed(2)} KB`;
    });

    socket.on("connect_error", () => {
        document.getElementById("cpuUsage").innerText = "Connection Error";
        document.getElementById("memoryUsage").innerText = "Connection Error";
        document.getElementById("diskUsage").innerText = "Connection Error";
        document.getElementById("bytesSent").innerText = "Connection Error";
        document.getElementById("bytesReceived").innerText = "Connection Error";
    });
});
