base=(2)
users=20

for i in $(seq 8 20);
do
    for k in "${base[@]}";
    do
        echo "Running experiment with $k users and seed $i"

        ssh -i /home/eduardo/.ssh/id_rsa_dionisio dionisio@10.3.77.15 'pkill python'
        ssh -i /home/eduardo/.ssh/id_rsa_dionisio dionisio@10.3.77.15 'docker restart mn.cloud-1'
        ssh -i /home/eduardo/.ssh/id_rsa_dionisio dionisio@10.3.77.15 "mkdir logs/$k"

        ssh -i /home/eduardo/.ssh/id_rsa_dionisio dionisio@10.3.77.15 "python workspace/drl-css/services/steering/source/app.py --seed=$k" &
        ssh -i /home/eduardo/.ssh/id_rsa_dionisio dionisio@10.3.77.15 "python workspace/drl-css/services/steering/source/monitors/container_monitor.py --url=10.3.77.15:30500/receive_data --interval=4" &

        python topology/run-cloud-only.py --users=$users --arr_rate=$k --seed=$k

        ssh -i /home/eduardo/.ssh/id_rsa_dionisio dionisio@10.3.77.15 'pkill python'
        ssh -i /home/eduardo/.ssh/id_rsa_dionisio dionisio@10.3.77.15 'docker restart mn.cloud-1'

        scp -i /home/eduardo/.ssh/id_rsa_dionisio dionisio@10.3.77.15:/home/dionisio/logs/$k/* logs/$k
        ssh -i /home/eduardo/.ssh/id_rsa_dionisio dionisio@10.3.77.15 "rm -r logs/$k"

        mn -c
        pkill xterm
        pkill chrome

        echo "Sleeping for 10 seconds"
        sleep 10
    done

    echo "Moving logs to logs-cloud-only-10min-10ms-$i"
    mkdir logs-cloud-only-10min-10ms-$i

    for k in "${base[@]}";
    do
        mv logs/$k logs-cloud-only-10min-10ms-$i/
    done

    chmod 777 -R logs-cloud-only-10min-10ms-$i

done

shutdown -h now
