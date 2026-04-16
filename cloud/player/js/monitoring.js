// QoE model - Eduardo S Gama
var videoQuality = 0;
var videoQuality_1 = 0;
var videoStartUpDelay = 0;
var videoEventStall = 0;
var videoHasStall = false;
var videoStallDuration = 0;
var K = 0;
var videoQualitySum = 0;
var videoQualitySwitch = 0;
var liveQoE = 0;
var representationId = {
    1: 200,
    2: 400,
    3: 600,
    4: 800,
    5: 1000,
    6: 1500,
    7: 2500,
    8: 4000,
    9: 8000,
    10: 12000
};

var textuser = ""

async function loadQoE(player, u) {
    var time = 2000;
    var apId = 1;
    var url = "";

    while (true) {
        await new Promise(r => setTimeout(r, time));
        apId = (apId)%3 + 1;
        url = 'http://143.106.73.50:30500/qoe.mpd?&qoe=' + liveQoE + '&u=' + u;

        await fetch(url)
    };
}

function ChunkQuality(quality, maxQuality){
    var a_1 = 0.976
    var a_2 = 143.2

    return a_1 * Math.log(a_2 * representationId[quality]/representationId[maxQuality]);
}

const initMonitoring = (player) => {

    player.on(dashjs.MediaPlayer.events.PLAYBACK_STARTED, function (event) {
        videoStartUpDelay = performance.now() / 1000
    });

    player.on("bufferStalled", function (e) {
        videoEventStall = performance.now();
        videoHasStall = true;
    });

    player.on("bufferLoaded", function (e) {
        if (videoHasStall) {
            videoStallDuration += (performance.now() - videoEventStall)/1000;
            videoHasStall = false;
        }
    });

    player.on("videoChunkReceived", function (e) {
        if (e.mediaType == 'video' &&
            e.chunk.segmentType == 'MediaSegment' &&
            e.chunk.index >= K) {

            var videoQ = e.chunk.quality;
            var videoMaxQuality = 10;
            K += 1;

            videoQuality_1 = ChunkQuality(videoQ+1, videoMaxQuality);

            if (videoQuality != 0 && !isNaN(videoQuality)) {
                videoQualitySum += videoQuality_1
                videoQualitySwitch += Math.abs(videoQuality_1 - videoQuality)

                liveQoE = (videoQualitySum - videoQualitySwitch - videoStallDuration)/K;

                console.log("-----------------")
                console.log(liveQoE)
            }

            videoQuality = videoQuality_1;
        }
    });

    // player.on(dashjs.MediaPlayer.events["PLAYBACK_ENDED"], () => {
    //     clearInterval(eventPoller);
    //     clearInterval(bitrateCalculator);
    //
    //     download("hello.txt", textuser);
    // });
    //
    // var eventPoller = setInterval(() => {
    //     var streamInfo = player.getActiveStream().getStreamInfo();
    //     var dashMetrics = player.getDashMetrics();
    //     var dashAdapter = player.getDashAdapter();
    //
    //     if (dashMetrics && streamInfo) {
    //         const periodIdx = streamInfo.index;
    //
    //         var repSwitch = dashMetrics.getCurrentRepresentationSwitch('video', true);
    //         var bufferLevel = dashMetrics.getCurrentBufferLevel('video', true);
    //         var bitrate = repSwitch ? Math.round(dashAdapter.getBandwidthForRepresentation(repSwitch.to, periodIdx) / 1000) : NaN;
    //         var adaptation = dashAdapter.getAdaptationForType(periodIdx, 'video', streamInfo);
    //         var currentRep = adaptation.Representation_asArray.find(function (rep) {
    //             return rep.id === repSwitch.to
    //         })
    //         var frameRate = currentRep.frameRate;
    //         var resolution = currentRep.width + 'x' + currentRep.height;
    //         document.getElementById('bufferLevel').innerText = bufferLevel + " secs";
    //         document.getElementById('framerate').innerText = frameRate + " fps";
    //         document.getElementById('reportedBitrate').innerText = bitrate + " Kbps";
    //         document.getElementById('resolution').innerText = resolution;
    //
    //         textuser += bufferLevel + " "  + bitrate + " " + resolution + "\n";
    //     }
    // }, 100);
}

function download(filename, text) {

    var element = document.createElement('a');
    element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text));
    element.setAttribute('download', filename);


    element.style.display = 'none';
    document.body.appendChild(element);

    element.click();

    document.body.removeChild(element);
}
