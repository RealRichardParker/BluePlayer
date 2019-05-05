var currently_playing = -1;
var length = -1;

function update(url, index) {
    url = "https://" + url;
    console.log("updating url to " + url);

	var myPlayer = amp('player', { /* Options */
            techOrder: ["azureHtml5JS", "flashSS", "html5FairPlayHLS","silverlightSS", "html5"],
            "nativeControlsForTouch": false,
            autoplay: true,
            controls: true,
            width: "640",
            height: "400",
            poster: ""
    }, function() {
            console.log('Good to go!');
            // add an event listener
			currently_playing = index;
			console.log("Set currently playing to: " + currently_playing);
			playButton = document.getElementById("playButton");
			playButton.innerHTML = "Pause"
            this.addEventListener('ended', function() {
                    console.log('Finished!');
                }
            );
            myPlayer.src([{
                src: url,
                type: "application/vnd.ms-sstr+xml"
		    }]);
        }
    )
    console.log("nani is going on");
}

function pauseOrPlay() {
	var myPlayer = amp('player', { /* Options */
            techOrder: ["azureHtml5JS", "flashSS", "html5FairPlayHLS","silverlightSS", "html5"],
            "nativeControlsForTouch": false,
            autoplay: true,
            controls: true,
            width: "640",
            height: "400",
        poster: ""
    }, function() {
			if(currently_playing == -1) {
				var randIndex = Math.floor(Math.random() *(length - 1)) + 1;
				button = document.getElementById(randIndex.toString());
				button.click();	
				player_loaded = true;
			}
			var playButton = document.getElementById("playButton");
            if(myPlayer.paused()) {
                myPlayer.play();
				playButton.innerHTML = "Pause"
            } 
            else {
                myPlayer.pause(); 
				playButton.innerHTML = "Play"
            }
        }
    )
} 

function prev() {
    currently_playing--;
	if (currently_playing == 0)
		currently_playing = length;
	button = document.getElementById(currently_playing.toString());
	button.click();
}

function next() {
	currently_playing++;
	if(currently_playing == length + 1)
		currently_playing = 1;
	console.log(currently_playing.toString());
	button = document.getElementById(currently_playing.toString());
	button.click();
}

function getLength() {
    length = parseInt(document.getElementById("length").textContent);
	currently_playing = -1;
	console.log("loaded document! got length: " + length);
	console.log(currently_playing);
}
