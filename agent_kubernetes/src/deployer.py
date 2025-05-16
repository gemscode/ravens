# Kubernetes deployment function
from kubernetes import client, config as k8s_config 
import os
import yaml

def deploy_to_kubernetes(kafka_topic: str):
    """Deploy Kafka consumer to Kubernetes."""
    # Load Kubernetes configuration
    try:
        k8s_config.load_kube_config()
    except:
        k8s_config.load_incluster_config()
    
    # Create deployment configuration
    deployment_name = f"kafka-consumer-{kafka_topic.replace('-', '')}"
    container = client.V1Container(
        name="kafka-consumer",
        image="your-registry/kafka-consumer:latest",  # Update with your image
        env=[
            client.V1EnvVar(name="KAFKA_TOPIC", value=kafka_topic),
            client.V1EnvVar(name="KAFKA_BOOTSTRAP_SERVERS", value="192.168.2.201:9092"),
            client.V1EnvVar(name="REDIS_NODES", value="127.0.0.1:7000,127.0.0.1:7001,127.0.0.1:7002")
        ]
    )
    
    # Create and deploy
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={"app": f"kafka-consumer-{kafka_topic}"}),
        spec=client.V1PodSpec(containers=[container])
    )
    
    spec = client.V1DeploymentSpec(
        replicas=1,
        selector=client.V1LabelSelector(
            match_labels={"app": f"kafka-consumer-{kafka_topic}"}
        ),
        template=template
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
        apps_v1_api.create_namespaced_deployment(
            namespace="default",
            body=deployment
        )
        return deployment_name
    except Exception as e:
        raise Exception(f"Kubernetes deployment failed: {str(e)}")

