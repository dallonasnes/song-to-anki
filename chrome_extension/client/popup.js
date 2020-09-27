let changeColor = document.getElementById('changeColor');

chrome.storage.sync.get('color', function(data) {
    changeColor.style.backgroundColor = data.color;
    changeColor.setAttribute('value', data.color);
});

changeColor.onclick = function(element) {
    element.preventDefault();
    let color = element.target.value;
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs){
        chrome.tabs.executeScript(
            tabs[0].id,
            {code: 'document.body.style.backgroundColor = "' + color + '";'}
        );
    });

    //send post request to server from new tab to avoid cors error
    const link1 = "https://google.com";
    chrome.tabs.create({ url: link1 , active: false}, function(tab) {
        chrome.runtime.sendMessage({action: 'makeAnki'}, function(response){
            chrome.tabs.remove(tab.id);

            
        });
      });

};

chrome.runtime.onMessage.addListener(
    function(request, sender, sendResponse) {
      let data = request.data;
      var bytes = new Uint8Array(data.length);
        for (var i=0; i<bytes.length; i++) {
        bytes[i] = data.charCodeAt(i);            
        }             
        var blob = new Blob([bytes], {type: "application/apkg"});
      var url = URL.createObjectURL(blob);
    chrome.downloads.download({
        url: url, // The object URL can be used as download URL
        filename: "test.apkg"
        //...
    });
      
      sendResponse({close: true});
    });