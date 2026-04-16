// QoE model - Eduardo S Gama
var videoQuality = 0
var videoQuality_1 = 0
var videoHasStall = 0
var videoStallDuration = 0     //Stall occurrences
var K = 0
var videoQualitySum = 0
var videoQualitySwitch = 0
var totalQoe = 0
var bufferLevel = 0
var throughput = 0
var videoMaxQuality = 14
var videoQ = 0
var cumulativeQoE = 0
var serverUrl = "mn.cloud-1"

window.usersqoe = []


var constant = {
    3000: [1.17605641518082, 70.2104195796215],
    5800: [0.985114183257978, 160.060803222170],
    7500: [0.926464623598867, 220.712321728703],
    12000: [0.835510579424116, 397.170110357625],
    17000: [0.778846765313748, 613.848433264037],
    22000: [0.741615909816603, 847.282723505478],
    25000: [0.724445949994823, 994.088410958813],
    30000: [0.701289016152584, 1248.53743508635],
}

var selectedServiceLocation = ""

var representationId = {
    1: 100,
    2: 200,
    3: 375,
    4: 550,
    5: 750,
    6: 1000,
    7: 1500,
    8: 3000,
    9: 5800,
    10: 7500,
    11: 12000,
    12: 17000,
    13: 22000,
    14: 25000,
    15: 30000
};


var a_1 = 0.701289016152584;
var a_2 = 1248.53743508635;

ForcePlay = (video) => {
    const promise = video.play();
    if (promise !== undefined) {
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


init = (abrstr, url, btrmax) => {

    a_1 = constant[btrmax][0];
    a_2 = constant[btrmax][1];
    videoMaxQuality = btrmax

    console.log(a_1, a_2)

    var video = document.querySelector("video");
    var player = dashjs.MediaPlayer().create();

    player.updateSettings({
        streaming: {
            abr: {
                ABRStrategy: abrstr,
                maxBitrate: {
                    video: btrmax
                }
            }
        }
    });

    player.initialize(video, url, true);

    window.player = player
    window.steering = null
    window.usersqoe = []
    
    onLoadQoE(player);
}

onLoadQoE = (player) => {
    player.on("bufferStalled", function (e) {
        videoHasStall = 1;
    });

    player.on("playbackEnded", function (e) {
        window.close();
    });

    player.on("videoChunkReceived", function (e) {
        if (e.mediaType == 'video' &&
            e.chunk.segmentType == 'MediaSegment') {


            console.log(e)

            videoQ = e.chunk.quality;
            videoStallDuration += videoHasStall

            K += 1;

            videoQuality_1 = ChunkQuality(videoQ + 1, videoMaxQuality);

            if (videoQuality != 0 && !isNaN(videoQuality)) {
                videoQualitySum += videoQuality_1
                videoQualitySwitch += Math.abs(videoQuality_1 - videoQuality)

                totalQoe = (videoQualitySum - videoQualitySwitch - videoStallDuration) / K;
                cumulativeQoE = (videoQualitySum - videoQualitySwitch - videoStallDuration)
            }

            videoQuality = videoQuality_1;

            bufferLevel = player.getBufferLength()

            throughput = player.getAverageThroughput('video')
            videoHasStall = 0;

            console.info(
                K, 
                totalQoe, 
                videoQuality_1, 
                videoQualitySwitch, 
                videoStallDuration, 
                bufferLevel, 
                throughput, 
                videoQ, 
                selectedServiceLocation,
                cumulativeQoE
            )

            window.usersqoe = [
                player.time(), 
                player.duration(), 
                throughput,
                videoQuality_1,
                totalQoe,
                cumulativeQoE,
                videoQ,
                representationId[videoQ],
                K,
                bufferLevel,
                videoStallDuration,
                serverUrl
            ]
        }
    });

    player.on(dashjs.MediaPlayer.events.CONTENT_STEERING_REQUEST_COMPLETED, function (e) {
        try {
            if (e) {
                if (e.currentSteeringResponseData) {
                    window.steering = e.currentSteeringResponseData
                    selectedServiceLocation = e.currentSteeringResponseData.pathwayPriority.toString()
                }
            }
        } catch (e) {
            console.error(e);
        }
    });

    player.on(dashjs.MediaPlayer.events.METRIC_ADDED, function (e) {
        // Check if the metric added is an HTTP request metric
        if (e.metric === 'HttpList' && e.value && e.value.type === 'MediaSegment') {
            // Extract the URL of the requested segment
            const segmentUrl = e.value.url;
    
            // Optionally, parse the URL to extract the server information
            serverUrl = new URL(segmentUrl).host;

            // Log or store the server information
            console.log(`Segment requested from server: ${serverUrl}`);
            console.log(serverUrl)
        }
    });
}

function text(url) {
    return fetch(url).then(res => res.text());
}

function ChunkQuality(quality, maxQuality) {
    return a_1 * Math.log(a_2 * representationId[quality] / maxQuality);
}
