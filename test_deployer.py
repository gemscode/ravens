from agent_kubernetes.src.deployer import deploy_to_kubernetes

# Simulate Streamlit UI call
deployment_name = deploy_to_kubernetes(
    topic="videos-views",
    use_local_infra=True  # Use Docker-hosted Kafka/Redis
)
print(f"Deployed: {deployment_name}")

