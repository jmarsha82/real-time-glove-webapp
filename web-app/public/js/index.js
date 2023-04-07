function subscribeStart() {  // starts the subscription process
                            // triggered from button in index.html
    $.ajax({
        type: "GET",
        url: "http://127.0.0.1:5000/subscribe-start",  //references api route in backend.py
        crossDomain: true,
        success: function () {
            const subButton = document.getElementById("subscribe-button");
            subButton.className = "btn btn-primary button-position disabled"
            setTimeout(readyToPlay, 3000); //on success sets a timeout on a function that
                                                   // displays a message that the letter buttons can be pressed
        },
        error: function () {
            const waitMessage = document.getElementById("wait-message");
            waitMessage.style.color = 'red';
            waitMessage.innerText = "Error Starting Subscription Service"
        }
    });
}

function readyToPlay() { // called from subscribeStart() to show message that letter button can be pressed
    const waitMessage = document.getElementById("wait-message");
    waitMessage.style.color = 'green';
    waitMessage.innerText = "Ready To Play";
}


function cloudStart(temp) { // triggered from button in index.html passes in the letter from button pushed
    const trueDiv = document.getElementById("response-text");
    trueDiv.className = "alert alert-warning display-margin";
    trueDiv.innerText = "Waiting For Response"
    $.ajax({
        type: "GET",
        url: "http://127.0.0.1:5000/cloud-start", //references api route in backend.py
        crossDomain: true,
        success: function (data) {
            setTimeout(function () {// on success it sets a timer for 5
                                            // seconds then calls mainLetterFind(letter being pushed) to check hand_data.txt
                mainLetterFind(temp)
            }, 5000);
            console.log(data);
            console.log("Inside success for Cloud Start")
        },
        error: function (result) {
            const waitMessage = document.getElementById("wait-message");
            waitMessage.style.color = 'red';
            waitMessage.innerText = "Error Starting Subscription Service"
        },

    });

}

function switcher(value) { // displays correct or incorrect based off value passed in from regex match in last function

    if (value === -1) {
        const falseDiv = document.getElementById("response-text");
        falseDiv.className = "alert alert-danger display-margin";
        falseDiv.innerText = "You Are Incorrect"
    } else {
        const trueDiv = document.getElementById("response-text");
        trueDiv.className = "alert alert-success display-margin";
        trueDiv.innerText = "You Got It!"
    }

}


function mainLetterFind(temp) { // has letter to check against letter that was sent
    const rawFile = new XMLHttpRequest();
    console.log("Inside Main Letter Find")
    let allText = '';
    rawFile.open("GET", 'hand_data.txt', true); //opens a file that the backend has written to in backend_sub.py
    rawFile.onreadystatechange = function () {
        if (rawFile.readyState === 4) {
            if (rawFile.status === 200 || rawFile.status === 0) { // if the file is found it it takes the letter passed in
                                                                    // and checks it against what is on hand_data.txt using regex matching
                console.log("Found txt file")
                allText = rawFile.responseText;
                const textAreaTag = document.getElementById("output");
                textAreaTag.innerHTML = allText;
                const re = new RegExp(temp, 'g');
                temp = allText.search(re);
                switcher(temp); // takes in one of two values depending on the match
            }
        }
        console.log(rawFile.status)
    };
    rawFile.send(null);
};
