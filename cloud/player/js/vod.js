
const ForcePlay = (video) => {
    const promise = video.play();
    if(promise !== undefined){
        promise.then(() => {
            // Autoplay started
            console.log("Video started !")
        }).catch(error => {
            // Autoplay was prevented.
            video.muted = true;
            video.play();
        });
    }
}

const init = () => {
    var video,
        player,
        // url = "https://dash.akamaized.net/akamai/bbb_30fps/bbb_30fps.mpd";
       url = "http://143.106.73.50:30500/akamai/bbb_30fps/bbb_30fps.mpd";
    video = document.querySelector("video");
    player = dashjs.MediaPlayer().create();

    player.initialize(video, url, true);

    window.player = player

    ForcePlay(video);
    initMobilityPattern(video, player, url);
    initMonitoring(player);
}

const initStaticUser = () => {
    var video,
        player,
        url = "https://dash.akamaized.net/akamai/bbb_30fps/bbb_30fps.mpd";
//        url = "http://143.106.73.17:30001/akamai/bbb_30fps/bbb_30fps.mpd";
    video = document.querySelector("video");
    player = dashjs.MediaPlayer().create();

    player.initialize(video, url, true);

    window.player = player

    ForcePlay(video);

}

const init_1 = async () => {

    var video,
        player,
        // url = "http://localhost:3030/akamai/bbb_30fps/bbb_30fps.mpd";
        url = "http://143.106.73.50:30500/akamai/bbb_30fps/bbb_30fps.mpd";
    video = document.querySelector("video");
    player = dashjs.MediaPlayer().create();

    console.log(url)

    player.initialize(video, url, true);

    window.player = player

    ForcePlay(video);
    initMobilityPattern_1(video, player, url);
    initMonitoring(player);
    loadQoE("12")
}
