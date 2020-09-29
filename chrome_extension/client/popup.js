let submit = document.getElementById('submit');
let songLangInput = document.getElementById('songLangInput');
let textAboveInput = document.getElementById("form").elements['textAboveInput'];
let form = document.getElementById("form");

/*
//TODO: dynamically populate the valid target lang options on the page on click
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
};

window.onload = async function(){
    await sleep(200);
    const lang1 = document.getElementsByClassName("langsmall-song")[0].innerText.trim().toLowerCase().split('\n')[0].trim().split('/')[0].trim();
    const lang2 = document.getElementsByClassName("langsmall-song")[1].innerText.trim().toLowerCase().split('\n')[0].trim().split('/')[0].trim();
    textAboveInput.innerHTML = textAboveInput.innerHTML + lang1 + " or " + lang2 + "<br><br>";
};
*/

function getMapping(){
  chrome.tabs.query({active: true, currentWindow: true}, function(tabs){
    chrome.tabs.executeScript(
        tabs[0].id,
        {file: "/getMapping.js",
         allFrames: true
        }
    );
  });
}

function handleInvalidTargetLangEntry(){
    alert("The langauge you're learning isn't on this page. Please go to the right page and try again.")
    window.close();
}

submit.onclick = function(element) {
    element.preventDefault();
    //save song target language to local storage, then get mapping
    let targetLang = songLangInput.value || "";
    chrome.storage.local.set({songLang: targetLang}, function(resp){
      getMapping();
    });
};

chrome.runtime.onMessage.addListener(
  function(request, sender, sendResponse){
      if (request.action === "savedMapping"){
        chrome.tabs.create({ url: "https://google.com" , active: false}, function(tab) {
          chrome.runtime.sendMessage({action: 'makeAnki'}, function(response){
              chrome.tabs.remove(tab.id);
              //also close the popup window
              window.close();
              sendResponse({close: true});
          });
        });
      }
      else if (request.action === "handleInvalidTargetLangEntry"){
        handleInvalidTargetLangEntry();
      }
      else if (request.action === "readyWithError"){
        chrome.tabs.create({ url: "https://google.com" , active: false}, function(tab) {
          chrome.runtime.sendMessage({action: 'logError', errData: request.errData, alertIndicator: request.alertIndicator}, function(response){
              chrome.tabs.remove(tab.id);
              sendResponse({close: true});
          });
        });
      }
  }
);