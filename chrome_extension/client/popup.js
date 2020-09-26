let changeColor = document.getElementById('changeColor');

chrome.storage.sync.get('color', function(data) {
    changeColor.style.backgroundColor = data.color;
    changeColor.setAttribute('value', data.color);
});

changeColor.onclick = function(element) {
    element.preventDefault();
    let color = element.target.value;
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs){
        chrome.tabs.executeScript(
            tabs[0].id,
            {code: 'document.body.style.backgroundColor = "' + color + '";'}
        );
    });
    //send post request to server
    const req = new XMLHttpRequest();
    const baseUrl = "http://localhost:8000/lyrics-to-anki";
    //would build lyrics here to pass in request
    const song_name = "test";
    const song_lang = "english";
    const lyrics = {"line 1": "line 11"};

    var data = {};
    data.song_name = song_name;
    data.song_lang = song_lang;
    data.lyrics = lyrics;
    var json = JSON.stringify(data);

    req.open("PUT", baseUrl, true);
    req.setRequestHeader("Content-type", "application/json; charset=utf-8");
    
    req.onload = function() {
        let text = JSON.parse(req.responseText);
        console.log(text);
        //Here need to use download library to download anki deck response on client
    }
    req.send(json);


};