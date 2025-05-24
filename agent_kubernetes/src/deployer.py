from kubernetes import client, config as k8s_config
import time
import re
import socket

def get_host_ip():
    """Get host machine's Docker bridge IP dynamically"""
    try:
        # Connect to a dummy address to determine default interface
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # Google Public DNS
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        print(f"Error getting host IP: {e}")
        return "192.168.2.200"  # Fallback

def deploy_to_kubernetes(topic: str, use_local_infra: bool = False):
    # Load k3s configuration
    k8s_config.load_kube_config(config_file="agent_deployment/k3s.yaml")
    
    # Sanitize topic name
    sanitized_topic = re.sub(r'[^a-z0-9-]', '-', topic.lower())
    
    # Environment configuration
    if use_local_infra:
        host_ip = get_host_ip()
        kafka_servers = f"{host_ip}:9092"
        redis_nodes = f"{host_ip}:6379"
        image_name = "docker.io/library/kafka-consumer:latest"
        redis_mode = "single"
    else:
        from agent_core.interfaces.config import AppConfig
        app_config = AppConfig()
        kafka_servers = app_config.kafka_bootstrap_servers
        redis_nodes = ",".join([f"{node.host}:{node.port}" for node in app_config.redis_nodes])
        image_name = app_config.processor_image
        redis_mode = "cluster"

    deployment_name = f"kafka-consumer-{sanitized_topic}"
    
    # Container configuration
    container = client.V1Container(
        name="kafka-consumer",
        image=image_name,
        image_pull_policy="Never",
        env=[
            client.V1EnvVar(name="KAFKA_TOPIC", value=topic),
            client.V1EnvVar(name="KAFKA_BOOTSTRAP_SERVERS", value=kafka_servers),
            client.V1EnvVar(name="REDIS_MODE", value=redis_mode),
            client.V1EnvVar(name="REDIS_NODES", value=redis_nodes),
            client.V1EnvVar(name="KAFKA_GROUP_ID", value="video-views-group")
        ]
    )
    
    # Deployment spec
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={"app": deployment_name}),
        spec=client.V1PodSpec(
            containers=[container],
            restart_policy="Always"
        )
    )
    
    spec = client.V1DeploymentSpec(
        replicas=1,
        selector=client.V1LabelSelector(match_labels={"app": deployment_name}),
        template=template,
        strategy=client.V1DeploymentStrategy(
            type="RollingUpdate",
            rolling_update=client.V1RollingUpdateDeployment(
                max_unavailable=0,
                max_surge=1
            )
        )
    )
    
    deployment = client.V1Deployment(
        api_version="apps/v1",
        kind="Deployment",
        metadata=client.V1ObjectMeta(name=deployment_name),
        spec=spec
    )
    
    # Create deployment
    apps_v1_api = client.AppsV1Api()
    try:
        # Delete existing deployment
        apps_v1_api.delete_namespaced_deployment(
            name=deployment_name,
            namespace="default",
            grace_period_seconds=0
        )
        time.sleep(2)
    except client.exceptions.ApiException:
        pass  # Ignore if deployment doesn't exist
    
    apps_v1_api.create_namespaced_deployment(
        namespace="default",
        body=deployment
    )
    return deployment_name

