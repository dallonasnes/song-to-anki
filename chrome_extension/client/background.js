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

const HOST = "http://localhost:8000/";

function logErrorAtServer(err, alertIndicator){
    const baseUrl = HOST + "log-client-error";
    const data = {
        ex: str(err),
        sendAlert: alertIndicator
    };

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
                //do nothing
            } else {
                console.log("Log error at server response has incorrect status code of : " + res.status + " with status text: " + res.statusText);
            }
        }).catch(err=>console.log(err));
};

function makeRequest(mapping, songName, songLang, pageUrl){
    const baseUrl = HOST + "lyrics-to-anki";
    const data = {
        song_name: songName,
        song_lang: songLang,
        lyrics: mapping,
        pageUrl: pageUrl
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
                throw Error("Server response to process lyrics from pageUrl: " + pageUrl + " has incorrect status code of : " + res.status + " with status text: " + res.statusText);
            }
        }).then(blob=>{
            chrome.downloads.download({
                url: URL.createObjectURL(blob),
                filename: songName + ".apkg"
                //...
            }, function(e){
                logErrorAtServer(e, false);
            });
        }).catch(err=>logErrorAtServer(err, true));
};


chrome.runtime.onMessage.addListener(
    function(request, sender, sendResponse) {
      if (request.action === "makeAnki"){
        let finalMap;
        let songName;
        let songLang;
        let pageUrl;
        //first get the mapping
        //on callback, then get the song name
        //on last callback, get song target lang and send request to server
        chrome.storage.local.get('mapping', function(data) {
            finalMap = data.mapping;
            chrome.storage.local.get('songName', function(data) {
                songName = data.songName;
                chrome.storage.local.get('songLang', function(data){
                    songLang = data.songLang;
                    chrome.storage.local.get('pageUrl', function(data){
                        pageUrl = data.pageUrl;
                        makeRequest(finalMap, songName, songLang, pageUrl);
                    });
                });
            });
        });
      }

      sendResponse({close: true});
    });