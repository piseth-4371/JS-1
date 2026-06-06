const accessKey = "kv5_fhbEr5Lr3OFbo8Nz7pBxYhuhdEOMazahk41GBAg";
const searchForm = document.getElementById("searchForm");
const searchBox = document.getElementById("searchBox");
const searchResult = document.getElementById("searchResult");
const showMoreBtn = document.getElementById("showMoreBtn");

let keyword = "";
let page = 1;

async function searchImages() {
    keyword = searchBox.value;
    const url = `https://api.unsplash.com/search/photos?page=${page}&query=${keyword}&client_id=${accessKey}&per_page=12`;

    const response  = await fetch(url);
    const data = await response.json();

    const results = data.results;

    if(page === 1){
        searchResult.innerHTML = " ";
    }
    results.map((results) =>{
        const image = document.createElement("img");
        image.src=results.urls.small;
        image.classList = "w-full h-57.5 object-cover rounded-md";
        const imageLink = document.createElement("a");
        imageLink.herf = results.links.html;
        imageLink.target = "_blank";

        imageLink.appendChild(image);
        searchResult.appendChild(imageLink);
    })
    showMoreBtn.style.display = "block";
}

searchForm.addEventListener("submit", (e) =>{
    e.preventDefault();
    page = 1;
    searchImages();
})

showMoreBtn.addEventListener("click", ()=>{
    page ++;
    searchImages();
})