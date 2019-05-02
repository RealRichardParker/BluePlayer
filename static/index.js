function update(url) {
    url = "https://" + url
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
    console.log("nani is going on")
}
