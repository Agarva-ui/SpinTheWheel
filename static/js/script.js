


const ctx = document.querySelector("#wheel").getContext("2d");
const dia = ctx.canvas.width;
const rad = dia / 2;
const PI = Math.PI;
const TAU = 2 * PI;
if (!sectors || sectors.length === 0) {
  console.warn("No prizes to draw!");
} else {
  const arc = TAU / sectors.length;
}

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

// Draw the wheel once on load
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
let rotationAmount = 5 * TAU + targetAngle; // 5 full spins + stop at right place

ctx.canvas.style.transition = "transform 4s ease-out";
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

}, 4000);
});

