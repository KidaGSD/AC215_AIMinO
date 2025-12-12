import os
import pulumi
import pulumi_docker_build as docker_build
from pulumi_gcp import artifactregistry
from pulumi import CustomTimeouts
import datetime

# 🔧 Get project info
project = pulumi.Config("gcp").require("project")
location = os.environ["GCP_REGION"]

# 🕒 Timestamp for tagging
timestamp_tag = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
# Push AIMinO images to the aimino-repository in Artifact Registry
repository_name = "aimino-repository"
registry_url = f"us-docker.pkg.dev/{project}/{repository_name}"

# Docker Build + Push -> AIMinO API Service (from AC215_AIMinO repo)
aimino_image_config = {
    "image_name": "aimino-api-service",
    # AC215_AIMinO repo is mounted at /AC215_AIMinO inside the deployment container
    "context_path": "/AC215_AIMinO",
    "dockerfile": "src/api_service/Dockerfile",
}

aimino_api_image = docker_build.Image(
    f'build-{aimino_image_config["image_name"]}',
    tags=[
        pulumi.Output.concat(
            registry_url,
            "/",
            aimino_image_config["image_name"],
            ":",
            timestamp_tag,
        )
    ],
    context=docker_build.BuildContextArgs(
        location=aimino_image_config["context_path"]
    ),
    dockerfile={
        "location": f'{aimino_image_config["context_path"]}/{aimino_image_config["dockerfile"]}'
    },
    platforms=[docker_build.Platform.LINUX_AMD64],
    push=True,
    opts=pulumi.ResourceOptions(
        custom_timeouts=CustomTimeouts(create="30m"),
        retain_on_delete=True,
    ),
)

pulumi.export("aimino-api-service-ref", aimino_api_image.ref)
pulumi.export("aimino-api-service-tags", aimino_api_image.tags)
