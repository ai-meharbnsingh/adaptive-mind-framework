# 04_Azure_Infrastructure/azure_setup.py
# Foundational script for Azure infrastructure setup - Session 10
# Manages resource group creation for the Adaptive Mind Framework

import os
import logging
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.core.exceptions import HttpResponseError

# Configure professional logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Load environment variables from a .env file for security
load_dotenv()


class AzureInfrastructureManager:
    """
    Manages the setup of foundational Azure resources for the Adaptive Mind project.
    This class handles authentication, resource group creation, and configuration.
    """

    def __init__(self):
        """
        Initializes the AzureInfrastructureManager, setting up credentials and clients.
        """
        self.subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
        self.resource_group_name = "rg-adaptive-mind-prod"
        self.location = "eastus"  # Standard enterprise location, can be configured

        if not self.subscription_id:
            error_msg = "AZURE_SUBSCRIPTION_ID not found in environment variables. Please set it in your .env file."
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info("🔐 Initializing Azure credentials...")
        try:
            # Uses environment variables for authentication (AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET)
            # This is the standard, secure way for service principal authentication in production.
            self.credential = DefaultAzureCredential()
            self.resource_client = ResourceManagementClient(self.credential, self.subscription_id)
            logger.info("✅ Azure credentials and resource client initialized successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Azure credentials: {e}")
            logger.error(
                "Ensure your environment is configured for Azure authentication (e.g., `az login` or service principal environment variables).")
            raise

    def create_resource_group(self) -> bool:
        """
        Creates the primary resource group for the Adaptive Mind project.

        A resource group is a container that holds related resources for an Azure solution.
        This is a critical first step for organizing all our cloud assets.

        Returns:
            bool: True if the resource group was created or already exists, False otherwise.
        """
        logger.info(f"Checking for resource group '{self.resource_group_name}' in location '{self.location}'...")

        try:
            # Check if the resource group already exists to make the script idempotent
            if self.resource_client.resource_groups.check_existence(self.resource_group_name):
                logger.warning(f"⚠️ Resource group '{self.resource_group_name}' already exists. No action taken.")
                return True

            logger.info(f"🚀 Creating resource group '{self.resource_group_name}'...")
            rg_params = {
                "location": self.location,
                "tags": {
                    "Project": "Adaptive Mind Framework",
                    "Environment": "Production",
                    "ManagedBy": "PythonSDK"
                }
            }
            self.resource_client.resource_groups.create_or_update(
                self.resource_group_name,
                rg_params
            )
            logger.info(f"✅ Successfully created resource group '{self.resource_group_name}'.")
            return True

        except HttpResponseError as e:
            logger.error(f"❌ An HTTP error occurred during resource group creation: {e.message}")
            return False
        except Exception as e:
            logger.error(f"❌ An unexpected error occurred: {e}")
            return False

    def get_resource_group_details(self) -> dict:
        """
        Retrieves details for the project's resource group.

        Returns:
            dict: A dictionary containing details of the resource group, or an empty dict on failure.
        """
        logger.info(f"🔍 Retrieving details for resource group '{self.resource_group_name}'...")
        try:
            rg = self.resource_client.resource_groups.get(self.resource_group_name)
            details = {
                "name": rg.name,
                "id": rg.id,
                "location": rg.location,
                "provisioning_state": rg.properties.provisioning_state,
                "tags": rg.tags
            }
            logger.info(f"✅ Successfully retrieved details for '{rg.name}'.")
            return details
        except HttpResponseError as e:
            logger.error(f"❌ Failed to get resource group details: {e.message}")
            return {}
        except Exception as e:
            logger.error(f"❌ An unexpected error occurred while fetching details: {e}")
            return {}


def main():
    """
    Main execution function to set up the foundational Azure infrastructure.
    """
    logger.info("=========================================================")
    logger.info("   Adaptive Mind Framework - Azure Infrastructure Setup  ")
    logger.info("=========================================================")
    logger.info("Starting Phase 1: Foundational Resource Group Creation")

    try:
        manager = AzureInfrastructureManager()

        # Step 1: Create the resource group
        success = manager.create_resource_group()

        if success:
            # Step 2: Verify and display details
            details = manager.get_resource_group_details()
            if details:
                logger.info("\n--- Resource Group Verification ---")
                for key, value in details.items():
                    logger.info(f"  {key.capitalize():<20}: {value}")
                logger.info("-----------------------------------")
                logger.info("✅ Foundational infrastructure setup is complete and verified.")
            else:
                logger.error("❌ Resource group created but verification failed.")
        else:
            logger.error("❌ Failed to create the foundational resource group. Aborting.")

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
    except Exception as e:
        logger.error(f"A critical error occurred during the setup process: {e}")


if __name__ == "__main__":
    # To run this script, you need to:
    # 1. Install required packages: pip install azure-identity azure-mgmt-resource python-dotenv
    # 2. Log in with Azure CLI: `az login`
    # 3. Or, set up a service principal and configure environment variables:
    #    - AZURE_CLIENT_ID
    #    - AZURE_CLIENT_SECRET
    #    - AZURE_TENANT_ID
    # 4. Create a .env file in the same directory with:
    #    - AZURE_SUBSCRIPTION_ID=<your_subscription_id>

    main()