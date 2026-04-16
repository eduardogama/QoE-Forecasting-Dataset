base=(2 3)
users=16

for i in $(seq 1 20);
do
    for k in "${base[@]}";
    do
        echo "Running experiment with $k users and seed $i"

        python run-edge-cloud.py --users=$users --arr_rate=$k --seed=$k

        mn -c
        pkill xterm
        pkill chrome

        sleep 3
    done

  echo "Moving logs to logs-edge-cloud-10min-$i"
  mkdir logs-edge-cloud-10min-$i

  for k in "${base[@]}";
  do
      mv logs/$k logs-edge-cloud-10min-$i/
      chmod 777 -R logs-edge-cloud-10min-$i/$k
  done

  sleep 10

done
