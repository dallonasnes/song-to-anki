function sendLogMessage(err, alertIndicator){
    //pass strings instead of errors
    chrome.runtime.sendMessage({action: 'readyWithError', errData: err.toString(), alertIndicator: alertIndicator.toString()}, function(response){
        //do nothing
    });
};

function filterLine(x){
    return (100 * parseInt(x.split('-')[1])) + parseInt(x.split('-')[2]);
  };

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
};

(async function routine(){
    let lyrics = document.getElementsByClassName("ltf");
    if (lyrics && lyrics[0]){
        if (lyrics.length < 2){
            //have to try to get the lyrics again, after clicking on the "show original lyrics" button
            try {
                document.getElementsByClassName("dottedlink")[1].click();
            } catch (error){
                //console.log(error);
            }
            //now get lyrics again after a quick break
            await sleep(500);
            lyrics = document.getElementsByClassName("ltf");
        }

        if (lyrics.length === 2){
            let mapping = [];
            let xa = Array.from(lyrics[1].getElementsByTagName('div'));
            let ya = Array.from(lyrics[0].getElementsByTagName('div'));

            //make sure the language matches the target language, else flip them
            let targetLang;
            chrome.storage.local.get('songLang', function(data){
                targetLang = data.songLang.toLowerCase().trim();
                //if a target lang was specified, make sure we get it right
                let foundTargetLang;
                let foundBaseLang;
                try {
                    foundBaseLang = document.getElementsByClassName("langsmall-song")[0].innerText.trim().toLowerCase().split('\n')[0].trim().split('/')[0].trim();
                    foundTargetLang = document.getElementsByClassName("langsmall-song")[1].innerText.trim().toLowerCase().split('\n')[0].trim().split('/')[0].trim();
                } catch (error){
                    //console.log(error);
                }

                //if the target lang is different, then we flip
                if (targetLang && !(targetLang.includes(foundTargetLang) || foundTargetLang.includes(targetLang))){
                    let temp = ya;
                    ya = xa;
                    xa = temp;

                    //now rearrange found base and found target lang to align with input target
                    let newTemp = foundTargetLang;
                    foundTargetLang = foundBaseLang;
                    foundBaseLang = newTemp;

                    //if still not equal, then user didn't enter a language on that page
                    //so we need to prompt them to fix it, then try again
                    if (!(targetLang.includes(foundTargetLang) || foundTargetLang.includes(targetLang))){
                        chrome.runtime.sendMessage({action: 'handleInvalidTargetLangEntry'}, function(response){
                            //do nothing here
                        });
                        return;
                    }

                } else {
                    targetLang = foundTargetLang;
                }

                //now re-write targetLang to local storage just to have the most up-to-date value
                chrome.storage.local.set({songLang: targetLang}, function(resp){
                    let song_lyrics = xa.map(a => a.innerText);
                    let tr_lyrics = ya.map(a => a.innerText);

                    let song_ids = xa.map(a => a.getAttribute("class"));
                    let tr_ids = ya.map(a => a.getAttribute("class"));

                    //if (song_lyrics.length != song_ids.length) alert("something's broken, dallon take a look");
                    //if (tr_lyrics.length != tr_ids.length) alert("something's broken, dallon take a look");

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
                            let tmpObj = {};
                            if (!(songLyric.includes('[') || trLyric.includes('[') | songLyric.includes('....') || trLyric.includes('....'))){
                                tmpObj[songLyric] = trLyric;
                                mapping.push(tmpObj);
                            }
                        }
                    }

                    //now save the mapping in local storage
                    chrome.storage.local.set({mapping: mapping}, function(resp) {
                        //once that completes, try to parse the songname from the text
                        let songname;
                        try {
                            songname = document.getElementsByClassName("song-node-info-album")[0].getElementsByTagName("a")[0].innerText;
                        } catch (error){
                            //console.log(error);
                            //try again to get it, this time from URL bar
                            try {
                                songname = window.location.href.slice(0, window.location.href.indexOf('.html')).split('/').pop();
                            } catch (er) {
                                //console.log(er);
                                sendLogMessage(new Error("Unable to parse songname from url " + window.location.href), true);
                            }
                        }

                        //now have to cleanse the song name of any punctuation and extra spaces
                        if (songname){
                            songname = songname.replace(/[.,\/#!$%\?^&\*;:{}=\-_`~()]/g,"").replace(/\s{2,}/g," ");
                        } else {
                            songname = "mySongLyrics";
                        }

                        //save songname to local storage
                        chrome.storage.local.set({songName: songname}, function(resp) {

                            //save pageUrl to local storage
                            chrome.storage.local.set({pageUrl: window.location.href}, function(resp){
                                //once that completes, send a runtime message to open next tab and send data
                                chrome.runtime.sendMessage({action: 'savedMapping'}, function(response){
                                    //do nothing here
                                });
                            });
                        });
                    });
                });
            });
        } else {
            /* This state is most likely to occur when icon is clicked on song-info page instead of song-translation page*/
            chrome.runtime.sendMessage({action: 'handleOnlyOneLangColumnDisplayed'}, function(response){
                //do nothing here
            });
            return;
        }
    }
})();
