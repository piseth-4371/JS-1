var btc = document.getElementById("bitcoin");
var eth = document.getElementById("ethereum");
var doge = document.getElementById("dogecoin");

var settings = {
    "async":true,
    "scrossDomain":true,
    "url":"https://api.coingecko.com/api/v3/simple/price?vs_currencies=usd&ids=bitcoin%2Cethereum%2Cdogecoin&names=Bitcoin%2CEthereum%2CDogecoin",
    "method": "GET",
    "headers": {}
}
$.ajax(settings).done(function(respones){
    btc.innerHTML = respones.bitcoin.usd;
    eth.innerHTML = respones.ethereum.usd;
    doge.innerHTML = respones.dogecoin.usd;
});