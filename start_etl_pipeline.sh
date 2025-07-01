#!/bin/bash

: '
Purpose:
- Run the complete ETL pipeline: extract → transform → load.

Usage:
- ./run_etl_pipeline.sh <RUN_GROUP> <RUN_NAME> <NAMESPACE>

Arguments:
- RUN_GROUP   : Logical data group (e.g., "pet-food")
- RUN_NAME    : Specific data name or category (e.g., "pet-dry-food")
- NAMESPACE   : Kubernetes namespace to run the jobs (e.g., "dev-ns")

Example:
- ./run_etl_pipeline.sh "pet-food" "pet-dry-food" "dev-ns"

Execution:
- Deploys each ETL stage using Helm.
- Each stage runs as a separate Helm release.

Data Handling:
- A PVC inspector pod is created per job release.
- Transfers data from the PVC pod to the local project folder.
'

set -e            # Exit immediately if a command exits with a non-zero status
set -o pipefail   # Return the exit status of the last command in the pipe that failed

RUN_GROUP="$1"
RUN_NAME="$2"
NAMESPACE="$3"

# Validate input arguments
if [[ -z "$RUN_GROUP" || -z "$RUN_NAME" || -z "$NAMESPACE" ]]; then
    echo -e "\n Missing arguments!"
    echo "USAGE:"
    echo "  ./run_etl_pipeline.sh <RUN_GROUP> <RUN_NAME> <NAMESPACE>"
    echo "e.g:"
    echo "  ./run_etl_pipeline.sh \"pet-food\" \"pet-dry-food\" \"dev-ns\""
    exit 1
fi

DATA_PATH="./data/${RUN_GROUP}/${RUN_NAME}"
CHART_PATH="./etl-chart-process"  # Path to the Helm charts folder
JOBS=("extract" "transform" "load")

# Create data directory if it doesn't exist
mkdir -p "$DATA_PATH"

for job in "${JOBS[@]}"; do
    RELEASE_NAME="stage-$job"
    VOLUME_NAME="vol-inspect-$job"
    
    echo "▶️ Running stage: $job"

    # Install Helm chart with the appropriate jobToRun value
    helm install "$RELEASE_NAME" "$CHART_PATH" --set "jobToRun=$job"

    # Wait for the job to complete
    echo "⏳ Waiting for job $RELEASE_NAME to complete..."
    kubectl wait --for=condition=complete --timeout=180s job/"$RELEASE_NAME" -n "$NAMESPACE"

    # Get the pod name associated with the job
    POD_NAME=$(kubectl get pods -n "$NAMESPACE" -l job-name="$RELEASE_NAME" -o jsonpath="{.items[0].metadata.name}")

    # Copy data from pod to local folder
    echo "📦 Copying data from pod $POD_NAME..."
    kubectl cp "$NAMESPACE/$POD_NAME:/app/data/${RUN_GROUP}" "$DATA_PATH" 2>&1 | grep -v "tar: removing leading"

    # Uninstall the Helm release to clean up resources
    echo "🧹 Uninstalling release $RELEASE_NAME..."
    helm uninstall "$RELEASE_NAME" -n "$NAMESPACE"

    echo "✅ Stage $job complete."
done

echo "🎉 ETL pipeline completed successfully!"
