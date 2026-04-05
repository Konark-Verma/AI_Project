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

currentPlan = data
renderResults(data)
initChat()

showMap(data.coords)

}



let currentPlan = null;

function appendChatMessage(text, sender) {
    const body = document.getElementById('chat-body')
    if (!body) return

    const messageCard = document.createElement('div')
    messageCard.className = `chat-message ${sender}`
    messageCard.innerHTML = `<p>${text.replace(/\n/g, '<br>')}</p>`
    body.appendChild(messageCard)
    body.scrollTop = body.scrollHeight
}

function getTripFromStorage() {
    const source = localStorage.getItem('source')
    const destination = localStorage.getItem('destination')
    if (!source || !destination) return null
    const travelers = parseInt(localStorage.getItem('travelers'), 10)
    const budget = parseFloat(localStorage.getItem('budget'))
    const days = parseInt(localStorage.getItem('days'), 10)
    if (Number.isNaN(travelers) || Number.isNaN(budget) || Number.isNaN(days)) return null
    let travelType = localStorage.getItem('travelType') || 'city'
    if (travelType === 'state') travelType = 'city'
    return { source, destination, travelers, budget, days, travel_type: travelType }
}

async function sendChatMessage(message) {
    const payload = { message, plan: currentPlan }
    const trip = getTripFromStorage()
    if (trip) payload.trip = trip
    const response = await fetch('/chat_api', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    })
    return response.json()
}

function initChat() {
    const chatBody = document.getElementById('chat-body')
    const chatForm = document.getElementById('chat-form')
    const chatMessage = document.getElementById('chat-message')
    if (!chatBody || !chatForm || !chatMessage) return

    chatBody.innerHTML = ''
    appendChatMessage('Ask me about your itinerary, transport, budget, weather, or attractions for this trip.', 'bot')

    chatForm.addEventListener('submit', async (event) => {
        event.preventDefault()
        const message = chatMessage.value.trim()
        if (!message) return

        appendChatMessage(message, 'user')
        chatMessage.value = ''
        const data = await sendChatMessage(message)
        appendChatMessage(data.reply, 'bot')

        if (data.replanned && data.plan) {
            if (data.trip) {
                localStorage.setItem('source', data.trip.source)
                localStorage.setItem('destination', data.trip.destination)
                localStorage.setItem('travelers', String(data.trip.travelers))
                localStorage.setItem('budget', String(data.trip.budget))
                localStorage.setItem('days', String(data.trip.days))
                localStorage.setItem('travelType', data.trip.travel_type || 'city')
            }
            currentPlan = data.plan
            renderResults(data.plan, data.previous_plan)
            showMap(data.plan.coords)
        }
    })
}

function budgetPlanPreview(plan) {
    const text = plan && plan.budget_plan ? plan.budget_plan : ''
    const line = text.split('\n')[0] || ''
    return line.length > 180 ? line.substring(0, 177) + '…' : line
}

function buildPlanComparison(previousPlan, newPlan) {
    if (!previousPlan || !newPlan) return ''
    return `
<div class="card plan-comparison">
<h3>Previous vs updated</h3>
<div class="comparison-grid">
<div class="comparison-col">
<h4>Before</h4>
<p><strong>Transport:</strong> ${previousPlan.transport || '—'}</p>
<p><strong>Type:</strong> ${(previousPlan.travel_type || 'city').toUpperCase()}</p>
<p><strong>Budget strategy:</strong> ${budgetPlanPreview(previousPlan).replace(/</g, '&lt;')}</p>
</div>
<div class="comparison-col">
<h4>After</h4>
<p><strong>Transport:</strong> ${newPlan.transport || '—'}</p>
<p><strong>Type:</strong> ${(newPlan.travel_type || 'city').toUpperCase()}</p>
<p><strong>Budget strategy:</strong> ${budgetPlanPreview(newPlan).replace(/</g, '&lt;')}</p>
</div>
</div>
</div>`
}

function renderResults(data, previousPlan){

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


const comparisonBlock = previousPlan ? buildPlanComparison(previousPlan, data) : ''

document.getElementById("results").innerHTML=
`${comparisonBlock}
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

if (window.__tripMapInstance) {
    try { window.__tripMapInstance.remove() } catch (e) {}
    window.__tripMapInstance = null
}

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
window.__tripMapInstance = map

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