# 04_Azure_Infrastructure/key_vault_manager.py
# Manages Azure Key Vault for secure secrets management - Session 10
# Part of the Adaptive Mind Framework infrastructure setup

import os
import logging
from azure.mgmt.keyvault import KeyVaultManagementClient
from azure.mgmt.keyvault.models import (
    VaultCreateOrUpdateParameters,
    VaultProperties,
    Sku,
    SkuName,
    AccessPolicyEntry,
    Permissions,
    SecretPermissions,
)
from azure.core.exceptions import HttpResponseError

# Configure professional logging (consistent with azure_setup.py)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class KeyVaultManager:
    """
    Manages the creation and configuration of Azure Key Vault for the Adaptive Mind project.
    Ensures secure storage of application secrets, connection strings, and buyer API keys.
    """

    def __init__(
        self, credential, subscription_id: str, resource_group_name: str, location: str
    ):
        """
        Initializes the KeyVaultManager.

        Args:
            credential: An Azure credential object (e.g., DefaultAzureCredential).
            subscription_id (str): The Azure subscription ID.
            resource_group_name (str): The name of the resource group to deploy into.
            location (str): The Azure region for the Key Vault.
        """
        self.credential = credential
        self.subscription_id = subscription_id
        self.resource_group_name = resource_group_name
        self.location = location
        self.keyvault_name = (
            f"kv-adaptive-mind-prod-{os.urandom(4).hex()}"  # Globally unique name
        )

        logger.info("Initializing Key Vault management client...")
        try:
            self.keyvault_client = KeyVaultManagementClient(
                self.credential, self.subscription_id
            )
            logger.info("✅ Key Vault management client initialized successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Key Vault management client: {e}")
            raise

    def create_key_vault(self) -> bool:
        """
        Creates or updates an Azure Key Vault with enterprise-grade security settings.

        The Key Vault is configured with:
        - Standard SKU for production use.
        - Soft delete and purge protection enabled to prevent accidental data loss.
        - Access policies for the current service principal to manage secrets.

        Returns:
            bool: True if the Key Vault was created or updated successfully, False otherwise.
        """
        logger.info(
            f"🚀 Preparing to create Key Vault '{self.keyvault_name}' in resource group '{self.resource_group_name}'..."
        )

        try:
            # Get the object ID of the current service principal or user
            # This is necessary to grant access policies to the entity running this script.
            # For a more robust solution, you would pass in specific object IDs for your app service's managed identity.
            # For now, we grant access to the creator.

            # This part is a bit complex. In a real CI/CD pipeline, you'd get the service principal object ID
            # from the environment. DefaultAzureCredential doesn't expose it directly.
            # For this setup script, we'll assume the user running it needs access.
            # A placeholder is used here; this will be refined with managed identities later.
            tenant_id = os.getenv("AZURE_TENANT_ID")
            client_id = os.getenv("AZURE_CLIENT_ID")

            if not tenant_id or not client_id:
                logger.warning(
                    "⚠️ AZURE_TENANT_ID or AZURE_CLIENT_ID not set. Access policy might not be correctly configured for the service principal."
                )
                # A placeholder for the object ID if not available. In a real scenario, this would cause failure.
                object_id = "00000000-0000-0000-0000-000000000000"
            else:
                # In a real scenario, you'd use `az ad sp show --id <client-id> --query objectId` to get this
                # We will add a placeholder and document that it needs to be updated.
                logger.info(
                    "Setting access policy for the current service principal (placeholder). This should be updated for specific identities in production."
                )
                # This is a complex part to automate without more context, so we'll make it explicit.
                # The principle is sound, though: grant specific permissions.
                object_id = os.getenv(
                    "AZURE_PRINCIPAL_OBJECT_ID"
                )  # Best practice: set this in .env
                if not object_id:
                    logger.error(
                        "❌ AZURE_PRINCIPAL_OBJECT_ID is not set. Cannot configure Key Vault access policy. Please set this environment variable."
                    )
                    return False

            vault_properties = VaultProperties(
                tenant_id=tenant_id,
                sku=Sku(name=SkuName.STANDARD),
                access_policies=[
                    AccessPolicyEntry(
                        tenant_id=tenant_id,
                        object_id=object_id,
                        permissions=Permissions(
                            secrets=[
                                SecretPermissions.GET,
                                SecretPermissions.LIST,
                                SecretPermissions.SET,
                                SecretPermissions.DELETE,
                                SecretPermissions.RECOVER,
                                SecretPermissions.PURGE,
                            ]
                        ),
                    )
                ],
                enable_soft_delete=True,
                soft_delete_retention_in_days=90,
                enable_purge_protection=True,
            )

            parameters = VaultCreateOrUpdateParameters(
                location=self.location,
                properties=vault_properties,
                tags={
                    "Project": "Adaptive Mind Framework",
                    "Environment": "Production",
                    "Purpose": "Secrets Management",
                },
            )

            poller = self.keyvault_client.vaults.begin_create_or_update(
                self.resource_group_name, self.keyvault_name, parameters
            )

            result = poller.result()
            logger.info(f"✅ Successfully created/updated Key Vault '{result.name}'.")
            logger.info(f"   Vault URI: {result.properties.vault_uri}")
            return True

        except HttpResponseError as e:
            logger.error(
                f"❌ An HTTP error occurred during Key Vault creation: {e.message}"
            )
            return False
        except Exception as e:
            logger.error(
                f"❌ An unexpected error occurred during Key Vault creation: {e}"
            )
            return False

    def get_key_vault_uri(self) -> str | None:
        """
        Retrieves the URI of the created Key Vault.

        Returns:
            str | None: The Key Vault URI if it exists, otherwise None.
        """
        logger.info(f"🔍 Retrieving URI for Key Vault '{self.keyvault_name}'...")
        try:
            vault = self.keyvault_client.vaults.get(
                self.resource_group_name, self.keyvault_name
            )
            return vault.properties.vault_uri
        except HttpResponseError:
            logger.warning(f"⚠️ Key Vault '{self.keyvault_name}' not found.")
            return None


def main():
    """
    Main execution function to demonstrate Key Vault creation.
    This would typically be called from a master deployment script.
    """
    logger.info("=========================================================")
    logger.info("   Adaptive Mind - Azure Key Vault Setup Module          ")
    logger.info("=========================================================")

    # This script depends on the resource group already being created.
    # We will instantiate it here for standalone testing.
    # In the final version, a master script will coordinate these managers.
    from azure_setup import AzureInfrastructureManager

    try:
        infra_manager = AzureInfrastructureManager()
        if not infra_manager.create_resource_group():
            logger.error(
                "❌ Prerequisite failed: Could not ensure resource group exists. Aborting Key Vault setup."
            )
            return

        # Now, create the Key Vault Manager using the established resources
        kv_manager = KeyVaultManager(
            credential=infra_manager.credential,
            subscription_id=infra_manager.subscription_id,
            resource_group_name=infra_manager.resource_group_name,
            location=infra_manager.location,
        )

        success = kv_manager.create_key_vault()

        if success:
            vault_uri = kv_manager.get_key_vault_uri()
            if vault_uri:
                logger.info("\n--- Key Vault Verification ---")
                logger.info(f"  Name: {kv_manager.keyvault_name}")
                logger.info(f"  URI: {vault_uri}")
                logger.info("  Security: Soft Delete & Purge Protection Enabled")
                logger.info("----------------------------")
                logger.info("✅ Azure Key Vault setup is complete and verified.")
            else:
                logger.error("❌ Key Vault created but verification failed.")
        else:
            logger.error("❌ Failed to create the Azure Key Vault.")

    except ImportError:
        logger.error(
            "❌ This script should be run in an environment where 'azure_setup' is available."
        )
    except Exception as e:
        logger.error(f"A critical error occurred: {e}")


if __name__ == "__main__":
    # To run this script, you'll need the same setup as azure_setup.py, PLUS:
    # 1. pip install azure-mgmt-keyvault
    # 2. An environment variable `AZURE_PRINCIPAL_OBJECT_ID` for the service principal
    #    you are using to run the script. This is required to set the initial access policy.
    #    You can get this by running: `az ad sp show --id <your-service-principal-client-id> --query id -o tsv`

    main()
