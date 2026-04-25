document.addEventListener("DOMContentLoaded", () => {
    let mediaRecorder;
    let audioChunks = [];
    
    const micBtn = document.getElementById("micBtn");
    const analyzeBtn = document.getElementById("analyzeBtn");
    const resultArea = document.getElementById("resultArea");
    const spotifyPlayer = document.getElementById("spotifyPlayer");
    const trackSwitcher = document.getElementById("trackSwitcher");

    // Handle Text Button Click
    analyzeBtn.addEventListener("click", async () => {
        const text = document.getElementById("userText").value;
        if (!text.trim()) return alert("Please type something first!");
        
        const response = await fetch("http://127.0.0.1:5000/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text })
        });
        const data = await response.json();
        renderResult(data);
    });

    // Handle Audio Recording
    micBtn.addEventListener("click", async () => {
        if (!mediaRecorder || mediaRecorder.state === "inactive") {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];
            mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);
            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                const formData = new FormData();
                formData.append("audio", audioBlob, "rec.wav");
                
                const response = await fetch("http://127.0.0.1:5000/analyze", {
                    method: "POST",
                    body: formData
                });
                const data = await response.json();
                renderResult(data);
            };
            mediaRecorder.start();
            micBtn.classList.add("recording");
        } else {
            mediaRecorder.stop();
            micBtn.classList.remove("recording");
        }
    });

    function renderResult(data) {
        console.log("Data received from server:", data);
        
        // 1. Reveal the result section
        resultArea.classList.remove("hidden");
        
        // 2. Update Text
        document.getElementById("moodTitle").innerText = `Mood: ${data.mood}`;
        document.getElementById("moodQuote").innerText = data.quote;

        // 3. Create Song Switcher Buttons
        trackSwitcher.innerHTML = "";
        data.playlists.forEach((url, index) => {
            const btn = document.createElement("button");
            btn.innerText = `Choice ${index + 1}`;
            btn.className = (index === 0) ? "active" : "";
            btn.onclick = () => {
                spotifyPlayer.src = url;
                document.querySelectorAll('.switcher button').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            };
            trackSwitcher.appendChild(btn);
        });

        // 4. Set Initial Player URL
        spotifyPlayer.src = data.playlists[0];

        // 5. Update Sidebar History
        const historyList = document.getElementById("historyList");
        historyList.innerHTML = "<h3>History</h3>" + data.history.map(h => `
            <div class="history-item">
                <strong>${h.mood}</strong> <small>${h.timestamp}</small>
                <p>${h.text.substring(0, 30)}...</p>
            </div>
        `).reverse().join("");
    }
});