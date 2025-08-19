# 04_Azure_Infrastructure/container_registry_setup.py
# Manages Azure Container Registry deployment - Session 10
# Part of the Adaptive Mind Framework infrastructure setup

import os
import logging
from azure.identity import DefaultAzureCredential
from azure.mgmt.containerregistry import ContainerRegistryManagementClient
from azure.mgmt.containerregistry.models import Registry, Sku, SkuName
from azure.core.exceptions import HttpResponseError

# Configure professional logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class ContainerRegistryManager:
    """
    Manages the deployment and configuration of Azure Container Registry (ACR)
    for the Adaptive Mind project.
    """

    def __init__(self, credential, subscription_id: str, resource_group_name: str, location: str):
        """
        Initializes the ContainerRegistryManager.

        Args:
            credential: An Azure credential object (e.g., DefaultAzureCredential).
            subscription_id (str): The Azure subscription ID.
            resource_group_name (str): The name of the resource group to deploy into.
            location (str): The Azure region for the container registry.
        """
        self.credential = credential
        self.subscription_id = subscription_id
        self.resource_group_name = resource_group_name
        self.location = location
        # ACR names must be globally unique and alphanumeric
        self.registry_name = f"acradaptivemindprod{os.urandom(4).hex()}"

        logger.info("Initializing Container Registry management client...")
        try:
            self.acr_client = ContainerRegistryManagementClient(self.credential, self.subscription_id)
            logger.info("✅ Container Registry management client initialized successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Container Registry management client: {e}")
            raise

    def create_container_registry(self) -> str | None:
        """
        Creates an Azure Container Registry with a premium SKU for enterprise features.

        Configuration includes:
        - Premium SKU: Enables geo-replication, content trust, and enhanced security.
        - Admin user enabled: For easy initial access from local Docker client and CI/CD.

        Returns:
            str | None: The login server URL of the registry if created, otherwise None.
        """
        logger.info(f"🚀 Preparing to create Container Registry '{self.registry_name}'...")

        registry_params = Registry(
            location=self.location,
            sku=Sku(name=SkuName.PREMIUM),  # Premium for geo-replication and security features
            admin_user_enabled=True,
            tags={
                "Project": "Adaptive Mind Framework",
                "Environment": "Production",
                "Purpose": "Application Container Images"
            }
        )

        try:
            poller = self.acr_client.registries.begin_create(
                self.resource_group_name,
                self.registry_name,
                registry_params
            )
            logger.info("... Container Registry creation in progress...")
            registry_result = poller.result()

            logger.info(f"✅ Successfully created Container Registry '{registry_result.name}'.")
            logger.info(f"   Login Server: {registry_result.login_server}")
            return registry_result.login_server

        except HttpResponseError as e:
            logger.error(f"❌ An HTTP error occurred during ACR creation: {e.message}")
            return None
        except Exception as e:
            logger.error(f"❌ An unexpected error occurred during ACR creation: {e}")
            return None

    def get_registry_credentials(self) -> dict:
        """
        Retrieves the admin credentials for the container registry.

        Returns:
            dict: A dictionary with 'username' and 'password' if successful, else an empty dict.
        """
        logger.info(f"🔑 Retrieving admin credentials for '{self.registry_name}'...")
        try:
            creds = self.acr_client.registries.list_credentials(
                self.resource_group_name,
                self.registry_name
            )
            credentials = {
                "username": creds.username,
                "password": creds.passwords[0].value
            }
            logger.info(f"✅ Successfully retrieved admin username for '{self.registry_name}'.")
            return credentials
        except HttpResponseError as e:
            logger.error(f"❌ Failed to retrieve ACR credentials: {e.message}")
            return {}
        except Exception as e:
            logger.error(f"❌ An unexpected error occurred while retrieving ACR credentials: {e}")
            return {}


def main():
    """
    Main execution function to demonstrate Azure Container Registry creation.
    """
    logger.info("=========================================================")
    logger.info("   Adaptive Mind - Azure Container Registry Setup Module ")
    logger.info("=========================================================")

    from azure_setup import AzureInfrastructureManager

    try:
        infra_manager = AzureInfrastructureManager()
        if not infra_manager.create_resource_group():
            logger.error("❌ Prerequisite failed: Resource group not available. Aborting ACR setup.")
            return

        acr_manager = ContainerRegistryManager(
            credential=infra_manager.credential,
            subscription_id=infra_manager.subscription_id,
            resource_group_name=infra_manager.resource_group_name,
            location=infra_manager.location
        )

        login_server = acr_manager.create_container_registry()

        if login_server:
            creds = acr_manager.get_registry_credentials()

            logger.info("\n--- Container Registry Verification ---")
            logger.info(f"  Registry Name: {acr_manager.registry_name}")
            logger.info(f"  Login Server URL: {login_server}")
            logger.info(f"  SKU: Premium")
            if creds:
                logger.info(f"  Admin Username: {creds['username']}")
                logger.info("  Admin Password: [REDACTED FOR SECURITY]")
            logger.info("---------------------------------------")
            logger.info("✅ Azure Container Registry setup is complete and verified.")
            logger.info("You can now log in using: docker login " + login_server)
        else:
            logger.error("❌ Failed to create the Azure Container Registry.")

    except (ValueError, ImportError) as e:
        logger.error(f"Configuration or import error: {e}")
    except Exception as e:
        logger.error(f"A critical error occurred: {e}")


if __name__ == "__main__":
    # To run this script, you will need:
    # 1. All prerequisites from previous scripts.
    # 2. pip install azure-mgmt-containerregistry

    main()