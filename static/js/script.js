const rainContainer = document.getElementById("rain-container");
const rainImages = [
  "../static/assets/bgl_better.webp",
  "../static/assets/bgl_better.webp",
  "../static/assets/bgl_better.webp",
  "../static/assets/bgl_better.webp"
]; // add as many as you like

function createRain() {
  const img = document.createElement("img");
  img.src = rainImages[Math.floor(Math.random() * rainImages.length)];
  img.classList.add("rain-image");

  // random horizontal position
  img.style.left = Math.random() * window.innerWidth + "px";
  // random animation duration
  img.style.animationDuration = (Math.random() * 3 + 3) + "s";
  // random size
  const size = Math.random() * 40 + 30;
  img.style.width = size + "px";
  img.style.height = size + "px";

  rainContainer.appendChild(img);

  // remove the element after animation ends
  img.addEventListener("animationend", () => {
    img.remove();
  });
}

// spawn new rain every 100ms
setInterval(createRain, 100);



const ctx = document.querySelector("#wheel").getContext("2d");
const dia = ctx.canvas.width;
const rad = dia / 2;
const PI = Math.PI;
const TAU = 2 * PI;
const arc = TAU / sectors.length;

// Keep the drawing function
function drawSector(sector, i) {
const ang = arc * i;
ctx.save();
ctx.beginPath();
ctx.fillStyle = sector.color;
ctx.moveTo(rad, rad);
ctx.arc(rad, rad, rad, ang, ang + arc);
ctx.lineTo(rad, rad);
ctx.fill();
ctx.translate(rad, rad);
ctx.rotate(ang + arc / 2);
ctx.textAlign = "right";
ctx.fillStyle = sector.text;
ctx.font = "bold 30px 'Lato', sans-serif";
ctx.fillText(sector.label, rad - 10, 10);
ctx.restore();
}

 sectors.forEach(drawSector);
// Keep the popup logic
const popup = document.getElementById("popup");
const popupText = document.getElementById("popup-text");
const closePopup = document.getElementById("close-popup");
closePopup.addEventListener("click", () => {
popup.style.display = "none";
popup.style.zIndex = -1;
});

// --- Keep and use this Socket.IO logic ---
const socket = io();

document.getElementById("spinButton").addEventListener("click", () => {
socket.emit("spin"); // tell server to spin
});

socket.on("wheelSpin", (data) => {
let targetIndex = data.index;
// Calculate the final angle. Add some full rotations for a nice spinning effect.
let targetAngle = (TAU / sectors.length) * (sectors.length - targetIndex) - (arc / 2);
let rotationAmount = 8 * TAU + targetAngle; // 5 full spins + stop at right place

ctx.canvas.style.transition = "transform 12s cubic-bezier(0.2, 0.8, 0.2, 1)";
ctx.canvas.style.transform = `rotate(${rotationAmount}rad)`;

// After the animation finishes, show the popup
setTimeout(() => {
    popupText.textContent = `🎉 The winner is: ${data.label}!`;
    popup.style.display = "flex";
    popup.style.zIndex = "10";

    // Optional: Reset the wheel's rotation without animation for the next spin
    setTimeout(() => {
        ctx.canvas.style.transition = "none";
        // Calculate the remainder rotation to reset to the original position
        const resetRotation = rotationAmount % TAU;
        ctx.canvas.style.transform = `rotate(${resetRotation}rad)`;
    }, 500);

}, 12000);
});

// Chat functionality
const chat = document.getElementById('chat');
const messageInput = document.getElementById('message');
const sendBtn = document.getElementById('send');

sendBtn.onclick = () => {
  const message = messageInput.value.trim();
  if (!message) return;

  socket.emit('send_message', { message });
  messageInput.value = '';
};

socket.on('receive_message', (data) => {
  const msgElem = document.createElement('div');
  msgElem.textContent = data.message;
  chat.appendChild(msgElem);
  chat.scrollTop = chat.scrollHeight; // auto-scroll to bottom
});

messageInput.addEventListener('keydown', (e) => {
  if(e.key === 'Enter') {
    e.preventDefault(); // prevent newline in input
    sendBtn.click();    // trigger send button
  }
});
