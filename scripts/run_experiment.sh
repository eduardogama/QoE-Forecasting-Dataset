for k in $(seq 5 15);
do
    python player/download-chrome.py

    ssh -i /root/.ssh/id_rsa_grifo_root grifo@10.3.77.120 "python workspace/drl-css/steering-service/source/app.py --seed=$k" &
    python ml-scenario-trainning-nocontainer.py --users=$k --seed=$k

    ssh -i /root/.ssh/id_rsa_grifo_root grifo@10.3.77.120 'pkill python'
    ssh -i /root/.ssh/id_rsa_grifo_root grifo@10.3.77.120 'docker restart cloud'

    # python ml-scenario-trainning-container.py --users=$k --seed=$k

    mn -c
    pkill xterm
    pkill chrome

    sleep 10
done
