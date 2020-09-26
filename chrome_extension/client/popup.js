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


    /*TODO:
        try to get this to run in the background because we need to run it from the active tab to get around CORS policy
        but we cannot run code in other tab from within this popup.js fn
    */


    //send post request to server from new tab to avoid cors error
    const link1 = "https://google.com";
    chrome.tabs.create({ url: link1 , active: false}, function(tab) {
        // Why do you query, when tab is already given?
        chrome.tabs.executeScript(tab.id, {file:"jquery.min.js"}, function(tab) {
          // This executes only after jQuery has been injected and executed
          chrome.tabs.executeScript(tab.id, 
                {
                    code: `
                    function getLyrics(){
                        return {"line 1": "line 11"};
                    }
                    // This executes only after your content script executes
                    //chrome.tabs.sendMessage(tab.id, {persona: "pippo"});
                    const req = new XMLHttpRequest();
                    const baseUrl = "http://localhost:8000/lyrics-to-anki";
                    //would build lyrics here to pass in request
                    const song_name = "test";
                    const song_lang = "english";
        
                    var data = {};
                    data.song_name = song_name;
                    data.song_lang = song_lang;
                    data.lyrics = getLyrics();
        
                    req.open("PUT", baseUrl, true);
                    req.setRequestHeader("Content-type", "application/json; charset=utf-8");
                    
                    req.onload = function() {
                        let text = JSON.parse(req.responseText);
                        alert(text);
                        //Here need to use download library to download anki deck response on client
                    }
                    req.send(JSON.stringify(data));`
                }
          );
        });
      });

    


};