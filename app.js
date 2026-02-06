import {
  COUNTRY_LANGUAGE_DATA,
  LANGUAGES,
  LANGUAGE_THRESHOLD,
} from "./data.js";

// UI element references.
const mapContainer = document.getElementById("map");
const languageList = document.getElementById("language-list");
const tooltip = document.getElementById("tooltip");

// Application state: selected languages + map data.
const state = {
  selectedLanguages: new Set(),
  worldFeatures: [],
};

// Color palette for eligible/ineligible countries.
const colorScale = {
  eligible: "#2f8f4e",
  ineligible: "#c9c9c9",
};

// UI Controls: render the language checkboxes.
const buildLanguageControls = () => {
  languageList.innerHTML = "";

  LANGUAGES.forEach((language) => {
    const wrapper = document.createElement("label");
    wrapper.className = "language-item";

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.value = language;
    checkbox.addEventListener("change", (event) => {
      if (event.target.checked) {
        state.selectedLanguages.add(language);
      } else {
        state.selectedLanguages.delete(language);
      }
      updateMapColors();
    });

    const text = document.createElement("span");
    text.textContent = language;

    wrapper.appendChild(checkbox);
    wrapper.appendChild(text);
    languageList.appendChild(wrapper);
  });
};

// Data handling: return language data for a given country (default to empty).
const getCountryLanguageStats = (countryName) =>
  COUNTRY_LANGUAGE_DATA[countryName] || {};

// Data handling: get the maximum percentage across selected languages.
const getMaxSelectedPercentage = (countryStats) => {
  if (state.selectedLanguages.size === 0) {
    return 0;
  }

  let maxPercentage = 0;
  state.selectedLanguages.forEach((language) => {
    const value = countryStats[language] || 0;
    if (value > maxPercentage) {
      maxPercentage = value;
    }
  });

  return maxPercentage;
};

// Business logic: determine if the country reaches the threshold.
const isCountryEligible = (countryName) => {
  const stats = getCountryLanguageStats(countryName);
  const maxPercentage = getMaxSelectedPercentage(stats);
  return maxPercentage >= LANGUAGE_THRESHOLD;
};

// UI: show tooltip on hover with all language percentages.
const renderTooltip = (event, countryName) => {
  const stats = getCountryLanguageStats(countryName);

  const rows = LANGUAGES.map((language) => {
    const value = stats[language] ?? 0;
    return `<div class="tooltip-row"><span>${language}</span><span>${value}%</span></div>`;
  }).join("");

  tooltip.innerHTML = `
    <div class="tooltip-title">${countryName}</div>
    <div class="tooltip-body">${rows}</div>
  `;

  tooltip.style.opacity = "1";
  const { clientX, clientY } = event;
  tooltip.style.left = `${clientX + 16}px`;
  tooltip.style.top = `${clientY + 16}px`;
};

const hideTooltip = () => {
  tooltip.style.opacity = "0";
};

// Map rendering: load the world map and draw SVG paths.
const createMap = async () => {
  const width = mapContainer.clientWidth;
  const height = mapContainer.clientHeight;

  const svg = d3
    .select(mapContainer)
    .append("svg")
    .attr("width", "100%")
    .attr("height", "100%")
    .attr("viewBox", `0 0 ${width} ${height}`)
    .attr("preserveAspectRatio", "xMidYMid meet");

  const projection = d3
    .geoNaturalEarth1()
    .fitSize([width, height], { type: "Sphere" });
  const path = d3.geoPath().projection(projection);

  const response = await fetch(
    "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json"
  );
  const worldData = await response.json();
  const countries = topojson.feature(worldData, worldData.objects.countries)
    .features;

  state.worldFeatures = countries;

  svg
    .append("path")
    .attr("class", "sphere")
    .attr("d", path({ type: "Sphere" }));

  svg
    .append("g")
    .attr("class", "countries")
    .selectAll("path")
    .data(countries)
    .join("path")
    .attr("d", path)
    .attr("class", "country")
    .attr("fill", (d) =>
      isCountryEligible(d.properties.name)
        ? colorScale.eligible
        : colorScale.ineligible
    )
    .on("mouseenter", (event, d) => {
      renderTooltip(event, d.properties.name);
    })
    .on("mousemove", (event, d) => {
      renderTooltip(event, d.properties.name);
    })
    .on("mouseleave", hideTooltip);
};

// Map rendering: update fill colors based on selections.
const updateMapColors = () => {
  const countries = d3.selectAll(".country");

  countries
    .transition()
    .duration(300)
    .attr("fill", (d) =>
      isCountryEligible(d.properties.name)
        ? colorScale.eligible
        : colorScale.ineligible
    );
};

// Responsive: rebuild the map when the container size changes.
const handleResize = () => {
  mapContainer.innerHTML = "";
  createMap();
};

buildLanguageControls();
createMap();
window.addEventListener("resize", handleResize);
