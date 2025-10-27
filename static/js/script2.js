// ================================
// 🌧️ RAIN EFFECT
// ================================
const rainContainer = document.getElementById("rain-container");
const rainImages = [
  "../static/assets/bgl_better.webp",
  "../static/assets/bgl_better.webp",
  "../static/assets/bgl_better.webp",
  "../static/assets/bgl_better.webp"
];

// Create a single raindrop (image)
function createRain() {
  const img = document.createElement("img");
  img.src = rainImages[Math.floor(Math.random() * rainImages.length)];
  img.classList.add("rain-image");

  // Randomized styling
  img.style.left = Math.random() * window.innerWidth + "px";
  img.style.animationDuration = (Math.random() * 3 + 3) + "s";

  const size = Math.random() * 40 + 30;
  img.style.width = size + "px";
  img.style.height = size + "px";

  rainContainer.appendChild(img);

  // Remove when animation ends
  img.addEventListener("animationend", () => img.remove());
}

// Spawn new raindrops every 100ms
setInterval(createRain, 100);


// ================================
// 🎯 SPIN WHEEL SETUP
// ================================
const ctx = document.querySelector("#wheel").getContext("2d");
const dia = ctx.canvas.width;
const rad = dia / 2;
const PI = Math.PI;
const TAU = 2 * PI;
const arc = TAU / sectors.length;

// Draw each wheel sector
function drawSector(sector, i) {
  const ang = arc * i;
  ctx.save();
  ctx.beginPath();
  ctx.fillStyle = sector.color;
  ctx.moveTo(rad, rad);
  ctx.arc(rad, rad, rad, ang, ang + arc);
  ctx.lineTo(rad, rad);
  ctx.fill();

  // Draw label
  ctx.translate(rad, rad);
  ctx.rotate(ang + arc / 2);
  ctx.textAlign = "right";
  ctx.fillStyle = sector.text;
  ctx.font = "bold 30px 'Lato', sans-serif";
  ctx.fillText(sector.label, rad - 10, 10);
  ctx.restore();
}

// Draw the full wheel
sectors.forEach(drawSector);


// ================================
// 🎉 POPUP LOGIC
// ================================
const popup = document.getElementById("popup");
const popupText = document.getElementById("popup-text");
const closePopup = document.getElementById("close-popup");

closePopup.addEventListener("click", () => {
  popup.style.display = "none";
  popup.style.zIndex = -1;
});


// ================================
// ⚡ SOCKET.IO EVENTS
// ================================
const socket = io();

// Spin button click
document.getElementById("spinButton").addEventListener("click", () => {
  socket.emit("spin_vip"); // Tell server to spin (VIP)
});

// Handle spin animation from server
socket.on("wheelSpin_vip", (data) => {
  const targetIndex = data.index;

  // Calculate target rotation
  const targetAngle = (TAU / sectors.length) * (sectors.length - targetIndex) - (arc / 2);
  const rotationAmount = 5 * TAU + targetAngle; // 5 full spins

  // Animate rotation
  ctx.canvas.style.transition = "transform 4s ease-out";
  ctx.canvas.style.transform = `rotate(${rotationAmount}rad)`;

  // Show popup after animation
  setTimeout(() => {
    popupText.textContent = `🎉 The winner is: ${data.label}!`;
    popup.style.display = "flex";
    popup.style.zIndex = "10";

    // Reset rotation after spin
    setTimeout(() => {
      ctx.canvas.style.transition = "none";
      const resetRotation = rotationAmount % TAU;
      ctx.canvas.style.transform = `rotate(${resetRotation}rad)`;
    }, 500);
  }, 4000);
});


// ================================
// 💬 CHAT FUNCTIONALITY
// ================================
const chat = document.getElementById("chat");
const messageInput = document.getElementById("message");
const sendBtn = document.getElementById("send");

// Send message
sendBtn.onclick = () => {
  const message = messageInput.value.trim();
  if (!message) return;

  socket.emit("send_message_vip", { message });
  messageInput.value = "";
};

// Receive message
socket.on("receive_message_vip", (data) => {
  const msgElem = document.createElement("div");
  msgElem.textContent = data.message;
  chat.appendChild(msgElem);
  chat.scrollTop = chat.scrollHeight; // Auto-scroll to bottom
});

// Press Enter to send
messageInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    sendBtn.click();
  }
});
