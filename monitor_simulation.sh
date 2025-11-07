#!/bin/bash
# Monitor the 1000-cell Yao network simulation

echo "================================================================================"
echo "YAO 1000-CELL NETWORK SIMULATION MONITOR"
echo "================================================================================"
echo ""

# Check if process is running
if ps aux | grep -q "[p]ython yao_network_direct.py"; then
    echo "✓ Simulation is RUNNING"
    echo ""

    # Show process info
    echo "Process info:"
    ps aux | grep "[p]ython yao_network_direct.py" | awk '{print "  PID: "$2"  CPU: "$3"%  MEM: "$4"%  TIME: "$10}'
    echo ""

    # Show log file size
    if [ -f yao_1000cell_run.log ]; then
        SIZE=$(du -h yao_1000cell_run.log | cut -f1)
        LINES=$(wc -l < yao_1000cell_run.log)
        echo "Log file: yao_1000cell_run.log ($SIZE, $LINES lines)"
        echo ""
    fi

    # Show latest progress
    echo "Latest output:"
    echo "--------------------------------------------------------------------------------"
    tail -30 yao_1000cell_run.log | grep -v "template cannot be redefined"
    echo "================================================================================"
    echo ""
    echo "Commands:"
    echo "  Watch live:    tail -f yao_1000cell_run.log"
    echo "  Kill sim:      pkill -f 'python yao_network_direct.py'"
    echo "  Re-run:        bash monitor_simulation.sh"
    echo "================================================================================"
else
    echo "✗ Simulation is NOT running"
    echo ""

    if [ -f yao_1000cell_run.log ]; then
        echo "Last log output:"
        echo "--------------------------------------------------------------------------------"
        tail -50 yao_1000cell_run.log | grep -v "template cannot be redefined"
        echo "================================================================================"

        # Check if completed
        if grep -q "ALL DONE" yao_1000cell_run.log; then
            echo ""
            echo "✓✓✓ SIMULATION COMPLETED SUCCESSFULLY! ✓✓✓"
            echo ""

            # Show results
            if [ -f yao_network_1000cells.pkl ]; then
                SIZE=$(du -h yao_network_1000cells.pkl | cut -f1)
                echo "Output file: yao_network_1000cells.pkl ($SIZE)"
            fi

            if [ -f yao_network_1000cells_traces.png ]; then
                echo "Plot file: yao_network_1000cells_traces.png"
            fi

            echo ""
            echo "View results:"
            echo "  python -c \"import pickle; d=pickle.load(open('yao_network_1000cells.pkl','rb')); print(d.keys())\""
            echo "================================================================================"
        else
            echo ""
            echo "⚠ Simulation may have stopped unexpectedly"
            echo "Check log: cat yao_1000cell_run.log"
        fi
    else
        echo "No log file found (yao_1000cell_run.log)"
    fi
fi
