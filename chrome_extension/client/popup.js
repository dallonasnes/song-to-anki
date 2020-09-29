let submit = document.getElementById('submit');
let songLangInput = document.getElementById('songLangInput');

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

submit.onclick = function(element) {
    element.preventDefault();
    //save song target language to local storage, then get mapping
    let targetLang = songLangInput.innerText || "";
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
  }
);