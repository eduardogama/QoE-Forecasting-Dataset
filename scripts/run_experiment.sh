REMOTE_USER="your_remote_user"
REMOTE_HOST="your.remote.host.or.ip"
SSH_KEY_PATH="/path/to/your/private_key"
REMOTE_PROJECT_PATH="workspace/drl-css"
REMOTE_TARGET="${REMOTE_USER}@${REMOTE_HOST}"

for k in $(seq 5 15);
do
    python player/download-chrome.py

    ssh -i "$SSH_KEY_PATH" "$REMOTE_TARGET" "python ${REMOTE_PROJECT_PATH}/steering-service/source/app.py --seed=$k" &
    python ml-scenario-trainning-nocontainer.py --users=$k --seed=$k

    ssh -i "$SSH_KEY_PATH" "$REMOTE_TARGET" 'pkill python'
    ssh -i "$SSH_KEY_PATH" "$REMOTE_TARGET" 'docker restart cloud'

    # python ml-scenario-trainning-container.py --users=$k --seed=$k

    mn -c
    pkill xterm
    pkill chrome

    sleep 10
done
