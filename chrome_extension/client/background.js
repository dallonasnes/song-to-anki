chrome.runtime.onInstalled.addListener(function (){
    chrome.storage.sync.set({color: '#3aa757'}, function() {
        console.log("The color is green.");
    });
    chrome.declarativeContent.onPageChanged.removeRules(undefined, function() {
        chrome.declarativeContent.onPageChanged.addRules([{
            conditions: [new chrome.declarativeContent.PageStateMatcher({
                pageUrl: {hostEquals: 'lyricstranslate.com'},
            })
        ],
            actions: [new chrome.declarativeContent.ShowPageAction()]
        }]);
    });
});


function getLyrics(){
    return {"line 1": "line 11"};
}

function makeRequest(){
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
        chrome.runtime.sendMessage({data: req.responseText}, function(response){
            console.log("finished");
        });
        //Here need to use download library to download anki deck response on client
    }
    req.send(JSON.stringify(data));
}

chrome.runtime.onMessage.addListener(
    function(request, sender, sendResponse) {
      if (request.action === "makeAnki"){
        makeRequest();
      }
      
      
      sendResponse({close: true});
    });