let changeColor = document.getElementById('changeColor');

function filterLine(x){
  return (100 * parseInt(x.split('-')[1])) + parseInt(x.split('-')[2]);
};

function buildMapping(){
  //build mapping here
    let mapping = {};
    let lyrics = document.getElementsByClassName("ltf");

    x = Array.from(lyrics[0].getElementsByTagName('div'));
    y = Array.from(lyrics[1].getElementsByTagName('div'));

    song_lyrics = x.map(a => a.innerText);
    tr_lyrics = y.map(a => a.innerText);

    song_ids = x.map(a => a.getAttribute("class"));
    tr_ids = y.map(a => a.getAttribute("class"));

    if (song_lyrics.length != song_ids.length) alert("something's broken, dallon take a look");
    if (tr_lyrics.length != tr_ids.length) alert("something's broken, dallon take a look");

    filtered_song_ids = song_ids.filter(a => a.includes("ll"));
    filtered_tr_ids = tr_ids.filter(a => a.includes("ll"));

    //take the intersection of both filtered arrays to get an array of all lyrics lines' tags
    all_ids = new Set();
    for(var x of new Set(filtered_song_ids)) if(new Set(filtered_tr_ids).has(x)) all_ids.add(x);
    all_ids = Array.from(all_ids).sort((a, b) => filterLine(a) - filterLine(b));

    for(var id of all_ids){
      if (song_ids.includes(id) && tr_ids.includes(id)){
        let songLyricIdx = song_ids.indexOf(id);
        let trLyricIdx = tr_ids.indexOf(id);

        let songLyric = song_lyrics[songLyricIdx];
        let trLyric = tr_lyrics[trLyricIdx];
        //if no [ in the lyrics then proceed
        if (!(songLyric.includes('[') || trLyric.includes('['))){
          mapping[songLyric] = trLyric;
        }
      }
    }

    return mapping;
};

function getMapping(){
  chrome.tabs.query({active: true, currentWindow: true}, function(tabs){
    chrome.tabs.executeScript(
        tabs[0].id,
        {code: `
            function filterLine(x){
              return (100 * parseInt(x.split('-')[1])) + parseInt(x.split('-')[2]);
            };

            let mapping = {};
            let lyrics = document.getElementsByClassName("ltf");
            if (lyrics && lyrics[0]){
                let xa = Array.from(lyrics[0].getElementsByTagName('div'));
                let ya = Array.from(lyrics[1].getElementsByTagName('div'));
            
                let song_lyrics = xa.map(a => a.innerText);
                let tr_lyrics = ya.map(a => a.innerText);
            
                let song_ids = xa.map(a => a.getAttribute("class"));
                let tr_ids = ya.map(a => a.getAttribute("class"));
            
                if (song_lyrics.length != song_ids.length) alert("something's broken, dallon take a look");
                if (tr_lyrics.length != tr_ids.length) alert("something's broken, dallon take a look");
            
                let filtered_song_ids = song_ids.filter(a => a.includes("ll"));
                let filtered_tr_ids = tr_ids.filter(a => a.includes("ll"));
            
                //take the intersection of both filtered arrays to get an array of all lyrics lines' tags
                let all_ids = new Set();
                for(var x of new Set(filtered_song_ids)) if(new Set(filtered_tr_ids).has(x)) all_ids.add(x);
                all_ids = Array.from(all_ids).sort((a, b) => filterLine(a) - filterLine(b));
            
                for(var id of all_ids){
                  if (song_ids.includes(id) && tr_ids.includes(id)){
                    let songLyricIdx = song_ids.indexOf(id);
                    let trLyricIdx = tr_ids.indexOf(id);
            
                    let songLyric = song_lyrics[songLyricIdx];
                    let trLyric = tr_lyrics[trLyricIdx];
                    //if no [ in the lyrics then proceed
                    if (!(songLyric.includes('[') || trLyric.includes('['))){
                      mapping[songLyric] = trLyric;
                    }
                  }
                }

                //now pass a message to runtime with the mapped value
                chrome.storage.local.set({mapping: mapping}, function(resp) {
                  console.log("got the mapping in local storage");
                  console.log("now going to get the song name");
                  let songName;
                  songName = prompt("enter the song name");
                  while (!songName){
                    //do nothing
                  }
                  if (songName){
                    //save it in local storage. then use the next callback
                    chrome.storage.local.set({songName: songName}, function(resp) {
                      let songLang;
                      songLang = prompt("enter the song target lang");
                      while (!songLang){
                        //do nothing
                      }
                      if (songLang){
                        //now we have all the data so can send the request
                        console.log("now going to send the request");
                      }
                    });
                  }
                  else {
                    alert("song name doesn't work!");
                  }
                });

            }
            
        `,
         allFrames: true
        }
    );
    const link1 = "https://google.com";
    chrome.tabs.create({ url: link1 , active: false}, function(tab) {
      chrome.runtime.sendMessage({action: 'makeAnki'}, function(response){
          chrome.tabs.remove(tab.id);
      });
    });
});
}

function getSongLang(){
  prompt("Enter the target language of the song");
}

chrome.storage.sync.get('color', function(data) {
    changeColor.style.backgroundColor = data.color;
    changeColor.setAttribute('value', data.color);
});

changeColor.onclick = function(element) {
    element.preventDefault();
    let color = element.target.value;

    //each of the three below methods passes data to the background script
    getMapping();
    //getSongName();
    //getSongLang();
    
    //send post request to server from new tab to avoid cors error
    /*const link1 = "https://google.com";
    chrome.tabs.create({ url: link1 , active: false}, function(tab) {
        chrome.runtime.sendMessage({action: 'makeAnki'}, function(response){
            chrome.tabs.remove(tab.id);
        });
      });*/

};
/*
chrome.runtime.onMessage.addListener(
    function(request, sender, sendResponse) {
      let blob = request.data;
      //var bytes = new Uint8Array(data.length);
        //for (var i=0; i<bytes.length; i++) {
        //bytes[i] = data.charCodeAt(i);            
        //}             
        //var blob = new Blob([bytes], {type: "application/apkg"});
      var url = URL.createObjectURL(blob);
    chrome.downloads.download({
        url: url, // The object URL can be used as download URL
        filename: "test.apkg"
        //...
    });
      
      sendResponse({close: true});
    });*/