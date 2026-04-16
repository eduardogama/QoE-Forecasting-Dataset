REMOTE_USER="your_remote_user"
REMOTE_HOST="your.remote.host.or.ip"
SSH_KEY_PATH="/path/to/your/private_key"
REMOTE_PROJECT_PATH="workspace/drl-css"
REMOTE_LOGS_PATH="/home/${REMOTE_USER}/logs"
REMOTE_MONITOR_URL="${REMOTE_HOST}:30500/receive_data"
REMOTE_TARGET="${REMOTE_USER}@${REMOTE_HOST}"

base=(2)
users=20

for i in $(seq 8 20);
do
    for k in "${base[@]}";
    do
        echo "Running experiment with $k users and seed $i"

        ssh -i "$SSH_KEY_PATH" "$REMOTE_TARGET" 'pkill python'
        ssh -i "$SSH_KEY_PATH" "$REMOTE_TARGET" 'docker restart mn.cloud-1'
        ssh -i "$SSH_KEY_PATH" "$REMOTE_TARGET" "mkdir logs/$k"

        ssh -i "$SSH_KEY_PATH" "$REMOTE_TARGET" "python ${REMOTE_PROJECT_PATH}/services/steering/source/app.py --seed=$k" &
        ssh -i "$SSH_KEY_PATH" "$REMOTE_TARGET" "python ${REMOTE_PROJECT_PATH}/services/steering/source/monitors/container_monitor.py --url=${REMOTE_MONITOR_URL} --interval=4" &

        python topology/run-cloud-only.py --users=$users --arr_rate=$k --seed=$k

        ssh -i "$SSH_KEY_PATH" "$REMOTE_TARGET" 'pkill python'
        ssh -i "$SSH_KEY_PATH" "$REMOTE_TARGET" 'docker restart mn.cloud-1'

        scp -i "$SSH_KEY_PATH" "${REMOTE_TARGET}:${REMOTE_LOGS_PATH}/$k/*" logs/$k
        ssh -i "$SSH_KEY_PATH" "$REMOTE_TARGET" "rm -r logs/$k"

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
