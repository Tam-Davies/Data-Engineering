#!/bin/bash
# Weekly statistics of historical forecasting accuracy

# Step 6.1: Download dataset (run once in terminal, not inside script)
# wget https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/IBMSkillsNetwork-LX0117EN-Coursera/labs/synthetic_historical_fc_accuracy.tsv

# Step 6.2: Extract last 7 days of accuracy values into scratch.txt
echo $(tail -7 synthetic_historical_fc_accuracy.tsv | cut -f6) > scratch.txt

# Load into array
week_fc=($(cat scratch.txt))

# Step 6.3: Convert negatives to positives
for i in {0..6}; do
  if [[ ${week_fc[$i]} -lt 0 ]]; then
    week_fc[$i]=$(( -1 * week_fc[$i] ))
  fi
done

# Initialize min and max
minimum=${week_fc[0]}
maximum=${week_fc[0]}

# Loop through array to find min and max
for item in "${week_fc[@]}"; do
   if [[ $minimum -gt $item ]]; then
     minimum=$item
   fi
   if [[ $maximum -lt $item ]]; then
     maximum=$item
   fi
done

# Output results
echo "minimum absolute error = $minimum"
echo "maximum absolute error = $maximum"
