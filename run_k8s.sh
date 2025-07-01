#!/bin/bash

set -e

echo "📦 Running scraper job..."
kubectl apply -f ./k8s/scraper-job.yml -n ns-scraper

echo "⏳ Waiting for scraper job to complete..."
kubectl wait --for=condition=complete job/scraper-runner -n ns-scraper

echo "📥 Extracting file path from job logs..."
get_pvc_path=$(kubectl logs job/scraper-runner -n ns-scraper | grep -oE 'app/data/[^ ]+' | head -n 1)
get_local_path=$(echo "${get_pvc_path}" | sed 's/^app\///')

echo "✅ Found PVC file: ${get_pvc_path}"
echo "✅ Will save to local path: ./${get_local_path}"

echo "🔍 Launching PVC debugger pod..."
kubectl apply -f ./k8s/pvc-debugger.yml -n ns-scraper

echo "⏳ Waiting for debugger pod to be ready..."
kubectl wait --for=condition=Ready pod/pvc-debugger -n ns-scraper

# Create local directory structure if it doesn't exist
mkdir -p "$(dirname "./${get_local_path}")"

echo "📥 Copying file from pod to local..."
kubectl cp ns-scraper/pvc-debugger:/${get_pvc_path} ./${get_local_path}

echo "🧹 Cleaning up resources..."
kubectl delete pod pvc-debugger -n ns-scraper
kubectl delete job scraper-runner -n ns-scraper

echo "✅ Done. File saved to ./${get_local_path}"
