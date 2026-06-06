let hrs = document.getElementById("hrs");
let min = document.getElementById("min");
let sec = document.getElementById("sec");


setInterval(()=>{

    let curentTime = new Date();
    hrs.innerHTML = (curentTime.getHours()<10?"0":"") + curentTime.getHours();
    min.innerHTML = (curentTime.getHours()<10?"0":"") + curentTime.getMinutes();
    sec.innerHTML = (curentTime.getHours()<10?"0":"") + curentTime.getSeconds();
}, 1000)

