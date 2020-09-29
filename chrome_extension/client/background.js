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

function makeRequest(mapping, songName, songLang){
    const baseUrl = "http://localhost:8000/lyrics-to-anki";

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
            return res.blob();
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
        console.log("now sending from the background script");
        let finalMap;
        chrome.storage.local.get('mapping', function(data) {
            finalMap = data.mapping;
            console.log("now have everything from the background script");
            makeRequest(finalMap, "test", "persian");
            sendResponse({close: true});
        });
      }
    });