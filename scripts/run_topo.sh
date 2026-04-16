base=(100)
directory_name='logs-multi-edge-cloud-10min-40ms-30u-dyn-k5-load-apache-ld25'


for i in $(seq 1 10);
do
    for k in "${base[@]}";
    do
        echo "Running experiment with $k users and seed $i"

        nohup python services/steering/source/monitors/node_monitor.py > monitor.out 2>&1 &
        # nohup python -u services/planner/online/main.py --seed=$k > planner.out 2>&1 &

        python topology/topo.py 10 20 2.0 $k $k

        mn -c
        pkill chrome

        docker stop mn.cloud-1 mn.edge1 mn.edge2 mn.edge3 mn.edge4
        docker rm mn.cloud-1 mn.edge1 mn.edge2 mn.edge3 mn.edge4

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

shutdown -h now
