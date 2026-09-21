#!/bin/bash
# Forecast accuracy script (generalized for all days)

# Clear and re‑initialize the TSV file with header
echo -e "year\tmonth\tday\tobs_temp\tfc_temp\taccuracy\taccuracy_range" > historical_fc_accuracy.tsv

# Skip header in rx_poc.log and process each line
tail -n +2 rx_poc.log | while read year month day obs_temp fc_temp; do
    # Extract numeric values from obs_temp and fc_temp
    obs=$(echo "$obs_temp" | grep -o '[0-9]\+' | head -1)
    fc=$(echo "$fc_temp" | grep -o '[0-9]\+' | head -1)

    # Calculate accuracy
    accuracy=$((obs - fc))

    # Assign accuracy label
    abs_accuracy=${accuracy#-}
    if [ "$abs_accuracy" -le 1 ]; then
        label="excellent"
    elif [ "$abs_accuracy" -le 2 ]; then
        label="good"
    elif [ "$abs_accuracy" -le 3 ]; then
        label="fair"
    elif [ "$abs_accuracy" -le 4 ]; then
        label="poor"
    else
        label="very poor"
    fi

    # Append results to TSV
    echo -e "$year\t$month\t$day\t$obs\t$fc\t$accuracy\t$label" >> historical_fc_accuracy.tsv
done

