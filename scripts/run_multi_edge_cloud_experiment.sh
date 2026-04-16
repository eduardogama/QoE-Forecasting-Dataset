base=(2 3 4 5 6)
users=30
directory_name='logs-multi-edge-cloud-10min-40ms-30u-dyn-k5-load-plan-reactive'

for i in $(seq 6 10);
do
    for k in "${base[@]}";
    do

        if [ "$k" -le 3 ]; then
            users=20
        elif [ "$k" -lt 6 ]; then
            users=30
        else
            users=40
        fi

        echo "Running experiment with $k users ($users) and seed $i"
        
        nohup python services/steering/source/monitors/node_monitor.py > monitor.out 2>&1 &
        nohup python -u services/planner/online/main.py --seed=$k > planner.out 2>&1 &
        
        python topology/run-multi-edge-cloud.py --users=$users --arr_rate=$k --seed=$k
        # python topology/run-multi-edge-cloud.py --users=$users --arr_rate=$k --seed=$k

        mn -c
        pkill xterm
        pkill chrome
        
        docker stop mn.cloud-1 mn.edge1 mn.edge2 mn.edge3
        docker rm mn.cloud-1 mn.edge1 mn.edge2 mn.edge3

        for ppid in $(ps -eo ppid,stat | grep 'Z' | awk '{print $1}'); do kill -9 $ppid; done && screen -ls | grep -o '[0-9]*\.' | sed 's/\.//' | xargs -I {} screen -X -S {} quit

        mv *.out logs/$k

        echo "Sleeping for 5 seconds"
        sleep 5
    done

    echo "Moving logs to $directory_name-$i"
    mkdir $directory_name-$i

    for k in "${base[@]}";
    do
        mv logs/$k $directory_name-$i/
    done

    chmod 777 -R $directory_name-$i

done

# shutdown -h now
