import { NeatGradient } from "./node_modules/@firecms/neat/dist/index.es.js";

window.addEventListener("DOMContentLoaded", () => {
  new NeatGradient({
    ref: document.getElementById("gradient"),

    colors: [
      { color: "#ffcaf4", enabled: true },
      { color: "#c4c0f6", enabled: true },
      { color: "#b7d9f6", enabled: true },
      { color: "#ffadef", enabled: true },
      { color: "#a59cf3", enabled: true }
    ],

    speed: 2,
    horizontalPressure: 3,
    verticalPressure: 3,

    waveFrequencyX: 2,
    waveFrequencyY: 2,
    waveAmplitude: 6,

    shadows: 0,
    highlights: 1,

    colorBrightness: 1,
    colorSaturation: 6,
    colorBlending: 8,

    backgroundColor: "#f4f1f8",
    backgroundAlpha: 1
  });
});