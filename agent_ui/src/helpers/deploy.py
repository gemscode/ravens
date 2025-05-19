# helpers/deploy.py
import logging
from kubernetes import client as k8s_client, config as k8s_config
from kubernetes.client.rest import ApiException
from agent_core.interfaces.config import AppConfig

config = AppConfig()
logger = logging.getLogger(__name__)

def deploy_resume_processor(user_id: str):
    """Deploy or update resume processor in Kubernetes"""
    try:
        k8s_config.load_kube_config()
        api = k8s_client.AppsV1Api()
        
        container = k8s_client.V1Container(
            name="resume-worker",
            image=config.processor_image,
            env=[
                k8s_client.V1EnvVar(name="ELASTIC_HOST", value=config.elastic_host),
                k8s_client.V1EnvVar(name="KAFKA_BROKERS", value=config.kafka_bootstrap_servers),
                k8s_client.V1EnvVar(name="GROK_API_KEY", value=config.grok_api_token),
                k8s_client.V1EnvVar(name="USER_ID", value=user_id)
            ]
        )
        
        deployment = k8s_client.V1Deployment(
            metadata=k8s_client.V1ObjectMeta(name=f"resume-processor-{user_id}"),
            spec=k8s_client.V1DeploymentSpec(
                replicas=1,
                selector=k8s_client.V1LabelSelector(
                    match_labels={"app": "resume-processor"}
                ),
                template=k8s_client.V1PodTemplateSpec(
                    metadata=k8s_client.V1ObjectMeta(
                        labels={"app": "resume-processor"}
                    ),
                    spec=k8s_client.V1PodSpec(containers=[container])
                )
            )
        )
        
        try:
            api.patch_namespaced_deployment(
                name=f"resume-processor-{user_id}",
                namespace="default",
                body=deployment
            )
            logger.info("Worker deployment updated")
            return True
        except ApiException as e:
            if e.status == 404:
                api.create_namespaced_deployment(namespace="default", body=deployment)
                logger.info("Worker deployment created")
                return True
            logger.error(f"Deployment failed: {str(e)}")
            return False
            
    except Exception as e:
        logger.error(f"Deployment error: {str(e)}")
        return False

