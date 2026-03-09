function planTrip(){

let source=document.getElementById("source").value
let destination=document.getElementById("destination").value
let travelers=document.getElementById("travelers").value
let budget=document.getElementById("budget").value
let days=document.getElementById("days").value

localStorage.setItem("source",source)
localStorage.setItem("destination",destination)
localStorage.setItem("travelers",travelers)
localStorage.setItem("budget",budget)
localStorage.setItem("days",days)

window.location.href="/result"

}



async function loadResults(){

let source=localStorage.getItem("source")
let destination=localStorage.getItem("destination")
let travelers=localStorage.getItem("travelers")
let budget=localStorage.getItem("budget")
let days=localStorage.getItem("days")

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
days:days
})

})

let data=await response.json()

renderResults(data)

showMap(data.coords)

}



function renderResults(data){

let placesHTML=""

data.places.forEach(p=>{
placesHTML+=`<li>${p}</li>`
})

let itineraryHTML=""

data.itinerary.forEach(i=>{
itineraryHTML+=`<li>${i}</li>`
})

document.getElementById("results").innerHTML=

`
<div class="card">

<h3>Recommended Transport (ML)</h3>
<p>${data.transport}</p>

</div>

<div class="card">

<h3>Budget Strategy (AI)</h3>
<p>${data.budget_plan}</p>

</div>

<div class="card">

<h3>Route</h3>
<p>${data.route.join(" → ")}</p>

</div>

<div class="card">

<h3>Distance</h3>
<p>${data.distance} km</p>

</div>

<div class="card">

<h3>Recommended Attractions</h3>
<ul>${placesHTML}</ul>

</div>

<div class="card">

<h3>AI Generated Itinerary</h3>
<ul>${itineraryHTML}</ul>

</div>

`

}



function showMap(coords){

let map=L.map('map').setView(coords[0],3)

L.tileLayer(
'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
).addTo(map)

coords.forEach(c=>{
L.marker(c).addTo(map)
})

let routeLine=L.polyline(coords,{
color:'#2E86C1',
weight:4
}).addTo(map)

map.fitBounds(routeLine.getBounds())

}