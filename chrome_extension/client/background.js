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
        }).catch(err=>alert(err));

};


chrome.runtime.onMessage.addListener(
    function(request, sender, sendResponse) {
      if (request.action === "makeAnki"){
        let mapping = {"hey": "hey there"}; 
        let songName = "test";
        let songLang = "english";

        /*chrome.storage.local.set({songLang: "english"}, function() {
            console.log("got the song lang");
        });

        chrome.storage.local.set({songName: "test"}, function() {
            console.log("got the song lang");
        });

        
        chrome.storage.local.get('songLang', function(data) {
            songLang = data.songLang;
        });

        chrome.storage.local.get('songName', function(data) {
            songName = data.songName;
        });*/

        chrome.storage.local.get('mapping', function(data) {
            mapping = data.mapping;
            console.log("sending request");
            makeRequest(mapping, songName, songLang);
        });

      }

      else if (request.dataType === "mapping"){
        chrome.storage.local.set({mapping: request.data}, function() {
            console.log("got the mapping");
            mapping = request.data;
            console.log(mapping);
        });
      }
      else if (request.dataType === "songName"){
        chrome.storage.sync.set({songName: request.data}, function() {
            console.log("got the song name");
        });
      }
      else if (request.dataType === "songLang"){
        chrome.storage.sync.set({songLang: request.data}, function() {
            console.log("got the song lang");
        });
      }

      sendResponse({close: true});
    });