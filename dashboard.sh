#!/bin/bash

SESSION="pi-dashboard"

# If already running, just attach
tmux has-session -t $SESSION 2>/dev/null
if [ $? -eq 0 ]; then
    tmux attach -t $SESSION
    exit
fi

# Start base session (empty shell)
tmux new-session -d -s $SESSION

# Split vertically for logs (bottom = 40%)
tmux split-window -v -p 70 -t $SESSION

# ----- TOP SECTION -----

# Select top pane
tmux select-pane -t $SESSION:0.0

# Split top pane horizontally (left = 30%)
tmux split-window -h -p 80 -t $SESSION:0.0

# Left pane: fastfetch refreshing
tmux send-keys -t $SESSION:0.0 \
'while true; do clear; fastfetch; sleep 5; done' C-m

# Right pane: btop
tmux send-keys -t $SESSION:0.1 "btop" C-m

# ----- BOTTOM SECTION -----

tmux send-keys -t $SESSION:0.2 \
"journalctl -f -u ugh.service -o cat | stdbuf -oL ccze -A" C-m

tmux attach -t $SESSION