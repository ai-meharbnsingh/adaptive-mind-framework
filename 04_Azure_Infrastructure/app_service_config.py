# 04_Azure_Infrastructure/app_service_config.py
# Manages Azure App Service Plan and App Service deployment - Session 10
# Part of the Adaptive Mind Framework infrastructure setup
# ENHANCED: Added Web App creation and configuration
# REVISION 2: Enabled System-Assigned Managed Identity for enhanced security.

import os
import logging
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from azure.mgmt.web import WebSiteManagementClient
from azure.mgmt.web.models import AppServicePlan, Site, SiteConfig, ManagedServiceIdentity, ManagedServiceIdentityType
from azure.core.exceptions import HttpResponseError

# Configure professional logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class AppServiceManager:
    """
    Manages the deployment and configuration of Azure App Service Plan and the Web App
    for the Adaptive Mind project.
    """

    def __init__(self, credential, subscription_id: str, resource_group_name: str, location: str):
        """
        Initializes the AppServiceManager.

        Args:
            credential: An Azure credential object (e.g., DefaultAzureCredential).
            subscription_id (str): The Azure subscription ID.
            resource_group_name (str): The name of the resource group to deploy into.
            location (str): The Azure region for the App Service Plan.
        """
        self.credential = credential
        self.subscription_id = subscription_id
        self.resource_group_name = resource_group_name
        self.location = location
        self.plan_name = "asp-adaptive-mind-prod"  # App Service Plan name
        # Web App names must be globally unique
        self.app_name = f"app-adaptive-mind-prod-{os.urandom(4).hex()}"

        logger.info("Initializing Web Site management client...")
        try:
            self.web_client = WebSiteManagementClient(self.credential, self.subscription_id)
            logger.info("✅ Web Site management client initialized successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Web Site management client: {e}")
            raise

    def create_app_service_plan(self) -> str | None:
        """
        Creates an Azure App Service Plan with a premium Linux SKU for production.

        Configuration includes:
        - Premium v2 SKU (P1v2): Provides production-grade features like VNet integration,
          private endpoints, and auto-scaling.
        - Linux OS: To host our Python-based containerized application.

        Returns:
            str | None: The ID of the App Service Plan if created, otherwise None.
        """
        logger.info(f"🚀 Preparing to create App Service Plan '{self.plan_name}'...")

        plan_params = AppServicePlan(
            location=self.location,
            reserved=True,  # This is required for Linux plans
            sku={
                "name": "P1v2",
                "tier": "PremiumV2",
                "size": "P1v2",
                "family": "Pv2",
                "capacity": 1  # Start with one instance, will auto-scale
            },
            kind="Linux",
            tags={
                "Project": "Adaptive Mind Framework",
                "Environment": "Production",
                "Purpose": "Application Hosting"
            }
        )

        try:
            # Making this idempotent by checking for existence first
            existing_plan = self.web_client.app_service_plans.get(self.resource_group_name, self.plan_name)
            if existing_plan:
                logger.warning(f"⚠️ App Service Plan '{self.plan_name}' already exists. Using existing plan.")
                return existing_plan.id
        except HttpResponseError as e:
            if e.status_code == 404:
                # Plan does not exist, proceed with creation
                pass
            else:
                raise

        try:
            poller = self.web_client.app_service_plans.begin_create_or_update(
                self.resource_group_name,
                self.plan_name,
                plan_params
            )
            logger.info("... App Service Plan creation in progress...")
            plan_result = poller.result()

            logger.info(f"✅ Successfully created App Service Plan '{plan_result.name}'.")
            return plan_result.id

        except HttpResponseError as e:
            logger.error(f"❌ An HTTP error occurred during App Service Plan creation: {e.message}")
            return None
        except Exception as e:
            logger.error(f"❌ An unexpected error occurred during App Service Plan creation: {e}")
            return None

    def create_web_app(self, app_service_plan_id: str, acr_login_server: str, acr_username: str, acr_password: str) -> \
    tuple[str, str] | None:
        """
        Creates the Web App (App Service) to host the containerized application.

        Args:
            app_service_plan_id (str): The resource ID of the App Service Plan.
            acr_login_server (str): The login server URL for the Azure Container Registry.
            acr_username (str): The admin username for ACR.
            acr_password (str): The admin password for ACR.

        Returns:
            tuple[str, str] | None: The default hostname and the principal ID of the managed identity, or None on failure.
        """
        logger.info(f"🚀 Preparing to create Web App '{self.app_name}'...")

        docker_image_name = f"{acr_login_server}/adaptive-mind-backend:latest"

        site_config = SiteConfig(
            app_settings=[
                {"name": "DOCKER_REGISTRY_SERVER_URL", "value": f"https://{acr_login_server}"},
                {"name": "DOCKER_REGISTRY_SERVER_USERNAME", "value": acr_username},
                {"name": "DOCKER_REGISTRY_SERVER_PASSWORD", "value": acr_password},
                {"name": "WEBSITES_ENABLE_APP_SERVICE_STORAGE", "value": "false"},
                {"name": "DATABASE_URL", "value": "@Microsoft.KeyVault(SecretUri=...)"},
                {"name": "TELEMETRY_DB_URL", "value": "@Microsoft.KeyVault(SecretUri=...)"},
            ],
            linux_fx_version=f"DOCKER|{docker_image_name}",
            always_on=True,
            ftps_state="FtpsOnly"
        )

        web_app_params = Site(
            location=self.location,
            server_farm_id=app_service_plan_id,
            site_config=site_config,
            https_only=True,
            identity=ManagedServiceIdentity(type=ManagedServiceIdentityType.SYSTEM_ASSIGNED),
            # AUDIT FIX: Enable Managed Identity
            tags={
                "Project": "Adaptive Mind Framework",
                "Environment": "Production",
                "Purpose": "Application Instance"
            }
        )

        try:
            poller = self.web_client.web_apps.begin_create_or_update(
                self.resource_group_name,
                self.app_name,
                web_app_params
            )
            logger.info("... Web App creation in progress...")
            web_app_result = poller.result()

            logger.info(
                f"✅ Successfully created Web App '{web_app_result.name}' with System-Assigned Managed Identity.")

            # The principal_id is the unique ID for this app's identity in Azure AD
            managed_identity_principal_id = web_app_result.identity.principal_id
            logger.info(f"   Managed Identity Principal ID: {managed_identity_principal_id}")

            return web_app_result.default_host_name, managed_identity_principal_id

        except HttpResponseError as e:
            logger.error(f"❌ An HTTP error occurred during Web App creation: {e.message}")
            return None
        except Exception as e:
            logger.error(f"❌ An unexpected error occurred during Web App creation: {e}")
            return None


# main function remains the same, but will need slight modification to handle the returned tuple
def main():
    """
    Main execution function to demonstrate creating the full App Service environment.
    """
    logger.info("=========================================================")
    logger.info("   Adaptive Mind - Azure App Service Setup (Full)        ")
    logger.info("=========================================================")

    from azure_setup import AzureInfrastructureManager
    from container_registry_setup import ContainerRegistryManager

    try:
        infra_manager = AzureInfrastructureManager()
        infra_manager.create_resource_group()

        acr_manager = ContainerRegistryManager(
            infra_manager.credential, infra_manager.subscription_id, infra_manager.resource_group_name,
            infra_manager.location
        )
        login_server = acr_manager.create_container_registry()
        acr_creds = acr_manager.get_registry_credentials()

        app_service_manager = AppServiceManager(
            infra_manager.credential, infra_manager.subscription_id, infra_manager.resource_group_name,
            infra_manager.location
        )

        plan_id = app_service_manager.create_app_service_plan()
        if plan_id:
            logger.info(f"✅ App Service Plan '{app_service_manager.plan_name}' is ready.")

            result = app_service_manager.create_web_app(
                plan_id, login_server, acr_creds['username'], acr_creds['password']
            )

            if result:
                app_hostname, principal_id = result
                logger.info("\n--- Full App Service Deployment Verification ---")
                logger.info(f"  Web App Name: {app_service_manager.app_name}")
                logger.info(f"  Default URL: https://{app_hostname}")
                logger.info(f"  Managed Identity Principal ID: {principal_id}")
                logger.info("---------------------------------------------")
                logger.info("✅ Azure App Service environment setup is complete and verified.")
            else:
                logger.error("❌ Failed to create the Web App.")
        else:
            logger.error("❌ Failed to create the Azure App Service Plan.")

    except (ValueError, ImportError) as e:
        logger.error(f"Configuration or import error: {e}")
    except Exception as e:
        logger.error(f"A critical error occurred: {e}")


if __name__ == "__main__":
    main()