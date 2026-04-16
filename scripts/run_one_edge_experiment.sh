REMOTE_USER="your_remote_user"
REMOTE_HOST="your.remote.host.or.ip"
SSH_KEY_PATH="/path/to/your/private_key"
REMOTE_PROJECT_PATH="workspace/drl-css"
REMOTE_LOGS_PATH="/home/${REMOTE_USER}/logs"
REMOTE_TARGET="${REMOTE_USER}@${REMOTE_HOST}"

base=(2 3 4)
users=20

for i in $(seq 1 20);
do
    for k in "${base[@]}";
    do
        mkdir logs/$k
        
        echo "Starting experiment with $k users and seed $i"

        ssh -i "$SSH_KEY_PATH" "$REMOTE_TARGET" 'pkill python'
        ssh -i "$SSH_KEY_PATH" "$REMOTE_TARGET" 'docker restart mn.cloud-1'

        ssh -i "$SSH_KEY_PATH" "$REMOTE_TARGET" "mkdir logs/$k"
        ssh -i "$SSH_KEY_PATH" "$REMOTE_TARGET" "python ${REMOTE_PROJECT_PATH}/services/steering/source/app.py --seed=$k" &

        python topology/run-one-edge.py --users=$users --arr_rate=$k --seed=$k

        ssh -i "$SSH_KEY_PATH" "$REMOTE_TARGET" 'pkill python'
        ssh -i "$SSH_KEY_PATH" "$REMOTE_TARGET" 'docker restart mn.cloud-1'

        scp -i "$SSH_KEY_PATH" -r "${REMOTE_TARGET}:${REMOTE_LOGS_PATH}/$k/*" logs/$k
        ssh -i "$SSH_KEY_PATH" "$REMOTE_TARGET" "rm -r logs/$k"

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
