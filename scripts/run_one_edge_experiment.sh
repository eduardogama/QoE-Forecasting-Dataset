base=(2 3 4)
users=20

for i in $(seq 1 20);
do
    for k in "${base[@]}";
    do
        mkdir logs/$k
        
        echo "Starting experiment with $k users and seed $i"

        ssh -i /root/.ssh/id_rsa_grifo_root grifo@10.3.77.120 'pkill python'
        ssh -i /root/.ssh/id_rsa_grifo_root grifo@10.3.77.120 'docker restart mn.cloud-1'

        ssh -i /root/.ssh/id_rsa_grifo_root grifo@10.3.77.120 "mkdir logs/$k"
        ssh -i /root/.ssh/id_rsa_grifo_root grifo@10.3.77.120 "python workspace/drl-css/services/steering/source/app.py --seed=$k" &

        python topology/run-one-edge.py --users=$users --arr_rate=$k --seed=$k

        ssh -i /root/.ssh/id_rsa_grifo_root grifo@10.3.77.120 'pkill python'
        ssh -i /root/.ssh/id_rsa_grifo_root grifo@10.3.77.120 'docker restart mn.cloud-1'

        scp -i /root/.ssh/id_rsa_grifo_root -r grifo@10.3.77.120:/home/grifo/logs/$k/* logs/$k
        ssh -i /root/.ssh/id_rsa_grifo_root grifo@10.3.77.120 "rm -r logs/$k"

        mn -c
        pkill xterm
        pkill chrome

        docker stop mn.edge1 && docker rm mn.edge1

        echo "Sleeping for 3 seconds"
        sleep 3

    done

    echo "Moving logs to logs-one-edge-10min-$i"
    mkdir logs-one-edge-10min-$i

    for k in "${base[@]}";
    do
        mv logs/$k logs-one-edge-10min-$i/
    done

    chmod 777 -R logs-one-edge-10min-$i

done
