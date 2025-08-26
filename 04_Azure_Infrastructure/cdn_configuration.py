# 04_Azure_Infrastructure/cdn_configuration.py
# Manages Azure CDN for global performance - Session 10
# Part of the Adaptive Mind Framework infrastructure setup

import os
import logging
from azure.mgmt.cdn import CdnManagementClient
from azure.mgmt.cdn.models import Profile, Sku, SkuName, Endpoint
from azure.core.exceptions import HttpResponseError

# Configure professional logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class PerformanceManager:
    """
    Manages the deployment of Azure CDN for global content delivery and performance.
    """

    def __init__(
        self, credential, subscription_id: str, resource_group_name: str, location: str
    ):
        """
        Initializes the PerformanceManager.

        Args:
            credential: An Azure credential object (e.g., DefaultAzureCredential).
            subscription_id (str): The Azure subscription ID.
            resource_group_name (str): The name of the resource group to deploy into.
            location (str): The Azure region for the resources.
        """
        self.credential = credential
        self.subscription_id = subscription_id
        self.resource_group_name = resource_group_name
        self.location = location  # CDN Profiles are global, but still require a location for metadata
        self.cdn_profile_name = "cdn-adaptive-mind-prod"
        self.cdn_endpoint_name = f"cdnep-adaptive-mind-{os.urandom(4).hex()}"

        logger.info("Initializing CDN management client...")
        try:
            self.cdn_client = CdnManagementClient(self.credential, self.subscription_id)
            logger.info("✅ CDN management client initialized successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to initialize CDN management client: {e}")
            raise

    def create_cdn_profile(self) -> Profile | None:
        """
        Creates an Azure CDN profile.

        Returns:
            Profile | None: The created CDN Profile object or None on failure.
        """
        logger.info(f"🚀 Creating CDN Profile '{self.cdn_profile_name}'...")
        try:
            profile = self.cdn_client.profiles.begin_create(
                self.resource_group_name,
                self.cdn_profile_name,
                Profile(
                    location="global",  # CDN profiles are global resources
                    sku=Sku(name=SkuName.STANDARD_MICROSOFT),
                    tags={
                        "Project": "Adaptive Mind Framework",
                        "Environment": "Production",
                    },
                ),
            ).result()
            logger.info(f"✅ Successfully created CDN Profile '{profile.name}'.")
            return profile
        except HttpResponseError as e:
            logger.error(f"❌ Failed to create CDN Profile: {e.message}")
            return None

    def create_cdn_endpoint(self, app_service_hostname: str) -> Endpoint | None:
        """
        Creates a CDN endpoint and points it to the App Service as the origin.

        Args:
            app_service_hostname (str): The hostname of the App Service (e.g., myapp.azurewebsites.net).

        Returns:
            Endpoint | None: The created CDN Endpoint object or None on failure.
        """
        logger.info(f"🚀 Creating CDN Endpoint '{self.cdn_endpoint_name}'...")
        try:
            endpoint = self.cdn_client.endpoints.begin_create(
                self.resource_group_name,
                self.cdn_profile_name,
                self.cdn_endpoint_name,
                Endpoint(
                    location=self.location,
                    origins=[
                        {"name": "appServiceOrigin", "host_name": app_service_hostname}
                    ],
                    is_https_allowed=True,
                    is_http_allowed=False,  # Enforce HTTPS
                    query_string_caching_behavior="IgnoreQueryString",  # Good for static assets
                    tags={
                        "Project": "Adaptive Mind Framework",
                        "Environment": "Production",
                    },
                ),
            ).result()
            logger.info(f"✅ Successfully created CDN Endpoint '{endpoint.name}'.")
            logger.info(f"   CDN Hostname: {endpoint.host_name}")
            logger.info("   Note: CDN propagation can take several minutes to hours.")
            return endpoint
        except HttpResponseError as e:
            logger.error(f"❌ Failed to create CDN Endpoint: {e.message}")
            return None


def main():
    """
    Main execution function to demonstrate CDN setup.
    """
    logger.info("=========================================================")
    logger.info("   Adaptive Mind - Azure CDN Setup for Global Performance")
    logger.info("=========================================================")

    # Import managers needed for this orchestration
    from azure_setup import AzureInfrastructureManager
    from container_registry_setup import ContainerRegistryManager
    from app_service_config import AppServiceManager

    try:
        # Full prerequisite chain for a realistic test
        infra_manager = AzureInfrastructureManager()
        infra_manager.create_resource_group()

        acr_manager = ContainerRegistryManager(
            infra_manager.credential,
            infra_manager.subscription_id,
            infra_manager.resource_group_name,
            infra_manager.location,
        )
        login_server = acr_manager.create_container_registry()
        acr_creds = acr_manager.get_registry_credentials()

        app_service_manager = AppServiceManager(
            infra_manager.credential,
            infra_manager.subscription_id,
            infra_manager.resource_group_name,
            infra_manager.location,
        )
        plan_id = app_service_manager.create_app_service_plan()
        app_hostname = app_service_manager.create_web_app(
            plan_id, login_server, acr_creds["username"], acr_creds["password"]
        )

        if not app_hostname:
            logger.error(
                "❌ Prerequisite failed: Web App not available. Aborting CDN setup."
            )
            return

        # Now, create the CDN
        perf_manager = PerformanceManager(
            credential=infra_manager.credential,
            subscription_id=infra_manager.subscription_id,
            resource_group_name=infra_manager.resource_group_name,
            location=infra_manager.location,
        )

        cdn_profile = perf_manager.create_cdn_profile()
        if cdn_profile:
            cdn_endpoint = perf_manager.create_cdn_endpoint(app_hostname)

            if cdn_endpoint:
                logger.info("\n--- Azure CDN Verification ---")
                logger.info(f"  CDN Profile Name: {cdn_profile.name}")
                logger.info(f"  CDN Endpoint Name: {cdn_endpoint.name}")
                logger.info(f"  CDN URL: https://{cdn_endpoint.host_name}")
                logger.info(f"  Origin Hostname: {cdn_endpoint.origins[0].host_name}")
                logger.info("  SKU: Standard Microsoft")
                logger.info("----------------------------")
                logger.info("✅ Azure CDN setup is complete.")

    except (ValueError, ImportError) as e:
        logger.error(f"Configuration or import error: {e}")
    except Exception as e:
        logger.error(f"A critical error occurred: {e}")


if __name__ == "__main__":
    # To run this script, you will need:
    # 1. All prerequisites from previous scripts.
    # 2. pip install azure-mgmt-cdn

    main()
