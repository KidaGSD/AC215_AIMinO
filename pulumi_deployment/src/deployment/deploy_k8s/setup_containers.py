import pulumi
from pulumi import ResourceOptions
import pulumi_kubernetes as k8s


def setup_containers(project, namespace, k8s_provider, ksa_name, app_name):
    """
    Deploy AIMinO API backend to the GKE cluster.

    - Uses the AIMinO image built by the deploy_images stack.
    - Exposes the FastAPI app on port 8000 inside the cluster.
    """
    # Get AIMinO image reference from deploy_images stack.
    # For self-managed backends (like your GCS bucket), the fully-qualified
    # stack name format is always "organization/<project>/<stack>".
    # Here:
    #   project = "deploy-images" (see deploy_images/Pulumi.yaml)
    #   stack   = "dev"           (you created it with `pulumi stack init dev`)
    images_stack = pulumi.StackReference("organization/deploy-images/deploy-images")
    aimino_tag = images_stack.get_output("aimino-api-service-tags")

    # AIMinO API Deployment (FastAPI on port 8000)
    api_deployment = k8s.apps.v1.Deployment(
        "aimino-api-deployment",
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name="aimino-api",
            namespace=namespace.metadata.name,
        ),
        spec=k8s.apps.v1.DeploymentSpecArgs(
            selector=k8s.meta.v1.LabelSelectorArgs(
                match_labels={"app": "aimino-api"},
            ),
            template=k8s.core.v1.PodTemplateSpecArgs(
                metadata=k8s.meta.v1.ObjectMetaArgs(
                    labels={"app": "aimino-api"},
                ),
                spec=k8s.core.v1.PodSpecArgs(
                    service_account_name=ksa_name,
                    containers=[
                        k8s.core.v1.ContainerArgs(
                            name="aimino-api",
                            image=aimino_tag.apply(lambda tags: tags[0]),
                            image_pull_policy="IfNotPresent",
                            ports=[
                                k8s.core.v1.ContainerPortArgs(
                                    container_port=8000,
                                    protocol="TCP",
                                )
                            ],
                            env=[
                                k8s.core.v1.EnvVarArgs(
                                    name="AIMINO_SERVER_PORT",
                                    value="8000",
                                ),
                                k8s.core.v1.EnvVarArgs(
                                    name="AIMINO_API_PREFIX",
                                    value="/api/v1",
                                ),
                                k8s.core.v1.EnvVarArgs(
                                    name="AIMINO_ALLOWED_ORIGINS",
                                    # Config expects JSON list or comma list; use JSON here
                                    value='["*"]',
                                ),
                                k8s.core.v1.EnvVarArgs(
                                    name="GEMINI_API_KEY",
                                    value_from=k8s.core.v1.EnvVarSourceArgs(
                                        secret_key_ref=k8s.core.v1.SecretKeySelectorArgs(
                                            name="aimino-gemini-secret",
                                            key="GEMINI_API_KEY",
                                        )
                                    ),
                                ),
                            ],
                        ),
                    ],
                ),
            ),
        ),
        opts=ResourceOptions(provider=k8s_provider, depends_on=[namespace]),
    )

    # ClusterIP service for AIMinO API
    api_service = k8s.core.v1.Service(
        "aimino-api-service",
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name="aimino-api",
            namespace=namespace.metadata.name,
        ),
        spec=k8s.core.v1.ServiceSpecArgs(
            type="ClusterIP",
            ports=[
                k8s.core.v1.ServicePortArgs(
                    port=8000,
                    target_port=8000,
                    protocol="TCP",
                )
            ],
            selector={"app": "aimino-api"},
        ),
        opts=ResourceOptions(provider=k8s_provider, depends_on=[api_deployment]),
    )

    return api_service
