function getTravelType(){
    // prefer stored value; else derive from query string
    let tt = localStorage.getItem('travelType');
    if (!tt) {
        const params = new URLSearchParams(window.location.search);
        tt = params.get('type') || 'city';
        // 'state' travel was removed; map legacy value to city.
        if (tt === 'state') tt = 'city';
        localStorage.setItem('travelType', tt);
    }
    // Safety net: handle legacy localStorage values or direct navigation.
    if (tt === 'state') {
        tt = 'city';
        localStorage.setItem('travelType', tt);
    }
    return tt;
}

function planTrip(){
    let source=document.getElementById("source").value
    let destination=document.getElementById("destination").value
    let travelers=document.getElementById("travelers").value
    let budget=document.getElementById("budget").value
    let days=document.getElementById("days").value
    let travelType=getTravelType();

    localStorage.setItem("source",source)
    localStorage.setItem("destination",destination)
    localStorage.setItem("travelers",travelers)
    localStorage.setItem("budget",budget)
    localStorage.setItem("days",days)
    localStorage.setItem("travelType", travelType)

    window.location.href="/result"
}




async function loadResults(){

let source=localStorage.getItem("source")
let destination=localStorage.getItem("destination")
let travelers=localStorage.getItem("travelers")
let budget=localStorage.getItem("budget")
let days=localStorage.getItem("days")

    let travelType = localStorage.getItem('travelType') || 'city';
    // 'state' travel was removed; map legacy value to city.
    if (travelType === 'state') travelType = 'city';
let response=await fetch("/plan",{
    method:"POST",
    headers:{
        "Content-Type":"application/json"
    },
    body:JSON.stringify({
        source:source,
        destination:destination,
        travelers:travelers,
        budget:budget,
        days:days,
        travelType: travelType
    })
})

let data=await response.json()

renderResults(data)

showMap(data.coords)

}



function renderResults(data){

let placesHTML=""

if (data.places && Array.isArray(data.places)) {
    data.places.forEach(p => {
        const formattedPlace = typeof p === 'string' ? `<li>${p}</li>` : `<li style='white-space: pre-wrap; line-height: 1.6; margin-bottom: 8px;'>${p}</li>`
        placesHTML += formattedPlace
    })
}

let itineraryHTML=""

if (data.itinerary && Array.isArray(data.itinerary)) {
    data.itinerary.forEach(i=>{
        itineraryHTML+=`<li>${i}</li>`
    })
}

let travelTypeText = data.travel_type ? `<p><strong>Type:</strong> ${data.travel_type.toUpperCase()}</p>` : '';
let notesHTML = '';
if (data.notes && data.notes.length) {
    notesHTML = `<div class="card"><h3>Important Notes & Tips</h3><ul>${data.notes.map(n=>`<li style='margin-bottom: 10px; line-height: 1.5;'>${n}</li>`).join('')}</ul></div>`;
}

let budgetPlanText = data.budget_plan || '';
// Safety net: older server responses may still include "Flights" even when transport != Flight.
if (data.transport && data.transport !== 'Flight') {
    if (data.transport === 'Train') {
        budgetPlanText = budgetPlanText.replace(/Flights:/g, 'Train:');
    } else {
        budgetPlanText = budgetPlanText.replace(/Flights:/g, `Transport (${data.transport}):`);
    }
}

let transportInfoHTML = '';
if (data.transport === 'Flight' && data.flights) {
    transportInfoHTML =
        `<div class="card"><h3>✈ Flight Information</h3>` +
        `<p><strong>Estimated Price:</strong> ${data.flights.price}</p>` +
        `<p><strong>Duration:</strong> ${data.flights.duration_range || data.flights.duration || 'Varies'}</p>` +
        `<p><strong>Airline:</strong> ${data.flights.airline}</p>` +
        `<p><small>${data.flights.note ? data.flights.note : 'Prices may vary based on booking date'}</small></p>` +
        `</div>`;
} else if (data.transport === 'Train' && data.train) {
    transportInfoHTML =
        `<div class="card"><h3>🚆 Train Information</h3>` +
        `<p><strong>Estimated Price:</strong> ${data.train.price}</p>` +
        `<p><strong>Duration:</strong> ${data.train.duration_range || 'Varies'}</p>` +
        `<p><strong>Recommended Class:</strong> ${data.train.recommended_class || 'Varies'}</p>` +
        `<p><small>${data.train.note ? data.train.note : ''}</small></p>` +
        `</div>`;
}


document.getElementById("results").innerHTML=
`
<div class="card">
<h3>Travel Type</h3>
${travelTypeText}
</div>
<div class="card">
<h3>Recommended Transport (ML)</h3>
<p><strong style='font-size: 1.2em;'>${data.transport}</strong></p>
</div>
<div class="card">
<h3>Budget Strategy (AI)</h3>
<p>${budgetPlanText.replace(/\n/g, '<br>')}</p>
</div>
${transportInfoHTML}
<div class="card">
<h3>Route</h3>
<p>${data.route.join(" → ")}</p>
</div>
<div class="card">
<h3>Distance</h3>
<p><strong>${data.distance} km</strong></p>
</div>
<div class="card">
<h3>Top Attractions & Sightseeing</h3>
<ul>${placesHTML}</ul>
</div>
<div class="card">
<h3>AI Generated Itinerary</h3>
<ul>${itineraryHTML}</ul>
</div>
${notesHTML}
`

}



function showMap(coords){

// Function to calculate intermediate waypoints along great circle route
function getGreatCircleRoute(start, end, steps = 50) {
    const lat1 = start[0] * Math.PI / 180;
    const lon1 = start[1] * Math.PI / 180;
    const lat2 = end[0] * Math.PI / 180;
    const lon2 = end[1] * Math.PI / 180;
    
    const waypoints = [];
    
    for (let i = 0; i <= steps; i++) {
        const f = i / steps; // fraction from 0 to 1
        const A = Math.sin((1 - f) * getDistance(lat1, lon1, lat2, lon2)) / Math.sin(getDistance(lat1, lon1, lat2, lon2));
        const B = Math.sin(f * getDistance(lat1, lon1, lat2, lon2)) / Math.sin(getDistance(lat1, lon1, lat2, lon2));
        
        const x = A * Math.cos(lat1) * Math.cos(lon1) + B * Math.cos(lat2) * Math.cos(lon2);
        const y = A * Math.cos(lat1) * Math.sin(lon1) + B * Math.cos(lat2) * Math.sin(lon2);
        const z = A * Math.sin(lat1) + B * Math.sin(lat2);
        
        const latWaypoint = Math.atan2(z, Math.sqrt(x * x + y * y)) * 180 / Math.PI;
        const lonWaypoint = Math.atan2(y, x) * 180 / Math.PI;
        
        waypoints.push([latWaypoint, lonWaypoint]);
    }
    
    return waypoints;
}

function getDistance(lat1, lon1, lat2, lon2) {
    return Math.acos(Math.sin(lat1) * Math.sin(lat2) + Math.cos(lat1) * Math.cos(lat2) * Math.cos(lon2 - lon1));
}

let map = L.map('map').setView(coords[0], 3)

L.tileLayer(
    'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
).addTo(map)

// Add markers for all waypoints (source, intermediate stops, destination)
coords.forEach((c, index) => {
    const isFirst = index === 0;
    const isLast = index === coords.length - 1;
    
    let markerColor = '#2E86C1'; // default blue
    let markerLabel = '';
    
    if (isFirst) {
        markerColor = '#27AE60'; // green for start
        markerLabel = 'START';
    } else if (isLast) {
        markerColor = '#E74C3C'; // red for end
        markerLabel = 'END';
    } else {
        markerColor = '#F39C12'; // orange for stops
        markerLabel = 'STOP';
    }
    
    L.circleMarker(c, {
        radius: 8,
        fillColor: markerColor,
        color: '#fff',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.8
    }).bindPopup(`<b>${markerLabel}</b><br>Lat: ${c[0].toFixed(2)}, Lon: ${c[1].toFixed(2)}`).addTo(map)
})

// Draw great circle routes for each segment
let allSegmentPoints = [];
for (let i = 0; i < coords.length - 1; i++) {
    const routeWaypoints = getGreatCircleRoute(coords[i], coords[i + 1], 80);
    allSegmentPoints.push(...routeWaypoints);
    
    L.polyline(routeWaypoints, {
        color: '#2E86C1',
        weight: 3,
        dashArray: '5, 5',
        opacity: 0.8
    }).addTo(map)
}

// Fit map to all segments
if (allSegmentPoints.length > 0) {
    const latlngs = allSegmentPoints.map(p => L.latLng(p[0], p[1]));
    map.fitBounds(L.latLngBounds(latlngs))
}

}