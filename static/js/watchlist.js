async function updateWatchlist(){

    const res = await fetch("/api/watchlist");
    const data = await res.json();

    let table = document.getElementById("watchlist");

    table.innerHTML = "";

    data.forEach(obj=>{
        table.innerHTML += `<tr>
            <td>${obj.spkid}</td>
            <td>${obj.threat_score.toFixed(3)}</td>
        </tr>`;
    });
}

setInterval(updateWatchlist,3000); // real-time refresh
updateWatchlist();