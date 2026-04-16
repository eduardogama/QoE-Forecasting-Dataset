var counter = 0;

const sleep = async (milliseconds) => {
    return new Promise(resolve => setTimeout(resolve, milliseconds))
}

const initMobilityPattern = async (video, player, url) => {

    var path = '/samples/ericsson/trace-driving.csv';
    var apId = 0;
    var returnedData;
    var jsonData;

    await RequestMobilityCsv('GET', path)
        .then(function (result) {
            returnedData = result;
        })
        .catch(function (err) {
            console.error('There was an error!', err.statusText);
        });

    jsonData = parseCsv(returnedData);

    var userMobility = TimestampSwitchCell(jsonData);

    userMobility.forEach((mob) => {
        console.log("Entrou")
        // await sleep(20000);
        //
        //     if (counter%4== 0) {
        //         apId = (apId == 2) ? 1 : 2;
        //         player.retrieveManifest(url + '?apId=' + apId, callback = () => {});
        //     }
        //
        //     counter++;
    });

}


const initMobilityPattern_1 = async (video, player, url) => {
    var apId = 1;
    while (true) {
        await sleep(2000);

        player.retrieveManifest(url + '?apId=', callback = () => {});
    };

}

const TimestampSwitchCell = (jsonData) => {
    var accessPoints = {};
    console.log(convertTime(jsonData[0].Timestamp.split('_')[1]), jsonData[0].CellID);
    for (var i = 1; i < jsonData.length-1; i++) {
        var cell1 = jsonData[i-1].CellID;
        var cell2 = jsonData[i].CellID;
        var timestamp1 = convertTime(jsonData[i-1].Timestamp.split('_')[1]);
        var timestamp2 = convertTime(jsonData[i].Timestamp.split('_')[1]);

        var timestamp = (timestamp2 + timestamp1)/2


        if (cell1 != cell2) {
            console.log(timestamp, cell1, cell2);
        }
    }

    return accessPoints;
}

const convertTime = (timestamp) => {
    return ( Number(timestamp.split('.')[0])*3600 + Number(timestamp.split('.')[1])*60 + Number(timestamp.split('.')[2]))*1000;
}

const RequestMobilityCsv = (method, url) => {
    return new Promise (function (resolve, reject) {
        var xhr = new XMLHttpRequest();

        xhr.onload = function () {
            if (this.status >= 200 && this.status < 300) {
                resolve(xhr.response);
            } else {
                    reject({
                        status: this.status,
                        statusText: xhr.statusText
                    });
                }
        };

        xhr.onerror = function () {
            reject({
                status: this.status,
                statusText: xhr.statusText
            });
        };

        xhr.open(method, url);
        xhr.send(null);
    });
}

const parseCsv = (csv) => {
    let lines = csv.split("\n");
    const header = lines.shift().split(",")

    lines.shift(); // get rid of definitions

    return lines.map(line => {
        const bits = line.split(",")
        let obj = {};

        header.forEach((h, i) => obj[h] = bits[i]); // or use reduce here
        return obj;
    })
};
