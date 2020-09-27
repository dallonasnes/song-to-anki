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
};

function base64ToArrayBuffer(base64) {
    var binaryString = window.atob(base64);
    var binaryLen = binaryString.length;
    var bytes = new Uint8Array(binaryLen);
    for (var i = 0; i < binaryLen; i++) {
       var ascii = binaryString.charCodeAt(i);
       bytes[i] = ascii;
    }
    return bytes;
 }

 var saveByteArray = (function () {
    var a = document.createElement("a");
    document.body.appendChild(a);
    a.style = "display: none";
    return function (data, name) {
        
        a.href = url;
        a.download = name;
        a.click();
        window.URL.revokeObjectURL(url);
    };
}());

function makeRequest(){
    const baseUrl = "http://localhost:8000/lyrics-to-anki";
    //would build lyrics here to pass in request
    const song_name = "test";
    const song_lang = "english";

    const data = {
        song_name: song_name,
        song_lang: song_lang,
        lyrics: getLyrics()
    }

    const options = {
        method: "PUT",
        body: JSON.stringify(data),
        headers: {
            'Content-Type': 'application/json'
        }
    };

    fetch(baseUrl, options)
        .then(res=>{
            return res.blob();
        }).then(blob=>{
            /*chrome.runtime.sendMessage({data: blob}, function(response){
                console.log("finished");
            });*/
            //var data = new Int8Array(blob.length);
            //var toDown = new Blob([blob], {type: "octet/stream"});
            var url = URL.createObjectURL(blob);
            alert(url);
            chrome.downloads.download({
                url: url, // The object URL can be used as download URL
                filename: "asdftest.apkg"
                //...
            }, function(e){
                alert(e);
            });
            //URL.revokeObjectURL(url);
            //download(blob, "myTest.apkg", "application/apkg")
        }).catch(err=>alert(err));

    /*const req = new XMLHttpRequest();
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
        alert(req.response);
        console.log(req)
        chrome.runtime.sendMessage({data: req.response}, function(response){
            console.log("finished");
        });
        //Here need to use download library to download anki deck response on client
    }
    req.send(JSON.stringify(data));*/
}

chrome.runtime.onMessage.addListener(
    function(request, sender, sendResponse) {
      if (request.action === "makeAnki"){
        makeRequest();
      }
      
      
      sendResponse({close: true});
    });