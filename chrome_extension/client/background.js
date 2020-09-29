chrome.runtime.onInstalled.addListener(function (){
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

function makeRequest(mapping, songName, songLang){
    const baseUrl = "http://localhost:8000/lyrics-to-anki";
    console.log("just made the request");
    const data = {
        song_name: songName,
        song_lang: songLang,
        lyrics: mapping
    }

    const options = {
        method: "PUT",
        body: JSON.stringify(data),
        headers: {
            'Content-Type': 'application/json'
        }
    };

    fetch(baseUrl, options)
        .then(res=> {
            if (res.status == 200){
                return res.blob();
            } else {
                throw Error("Response has incorrect status code of : " + res.status + " with status text: " + res.statusText);
            }
        }).then(blob=>{
            chrome.downloads.download({
                url: URL.createObjectURL(blob),
                filename: songName + ".apkg"
                //...
            }, function(e){
                console.log(e);
            });
        }).catch(err=>console.log(err));
};


chrome.runtime.onMessage.addListener(
    function(request, sender, sendResponse) {
      if (request.action === "makeAnki"){
        let finalMap;
        let songName;
        let songLang;
        //first get the mapping
        //on callback, then get the song name
        //on last callback, get song target lang and send request to server
        chrome.storage.local.get('mapping', function(data) {
            finalMap = data.mapping;
            chrome.storage.local.get('songName', function(data) {
                songName = data.songName;
                chrome.storage.local.get('songLang', function(data){
                    songLang = data.songLang;
                    makeRequest(finalMap, songName, songLang);
                });
            });
        });
      }

      sendResponse({close: true});
    });