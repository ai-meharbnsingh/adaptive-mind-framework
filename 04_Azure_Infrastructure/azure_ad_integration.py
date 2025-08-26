# 04_Azure_Infrastructure/azure_ad_integration.py
# Manages Azure AD (Entra ID) integration for enterprise authentication - Session 10
# Part of the Adaptive Mind Framework infrastructure setup

import os
import logging
from azure.mgmt.web import WebSiteManagementClient
from azure.mgmt.web.models import SiteAuthSettings
from azure.core.exceptions import HttpResponseError

# Configure professional logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class AzureADManager:
    """
    Manages the configuration of Azure Active Directory authentication for the Web App.
    """

    def __init__(self, credential, subscription_id: str, resource_group_name: str):
        """
        Initializes the AzureADManager.

        Args:
            credential: An Azure credential object (e.g., DefaultAzureCredential).
            subscription_id (str): The Azure subscription ID.
            resource_group_name (str): The name of the resource group where the App Service resides.
        """
        self.credential = credential
        self.subscription_id = subscription_id
        self.resource_group_name = resource_group_name

        logger.info("Initializing Web Site management client for Auth operations...")
        try:
            self.web_client = WebSiteManagementClient(
                self.credential, self.subscription_id
            )
            logger.info(
                "✅ Web Site management client initialized successfully for Auth."
            )
        except Exception as e:
            logger.error(f"❌ Failed to initialize Web Site management client: {e}")
            raise

    def enable_azure_ad_authentication(self, app_name: str) -> bool:
        """
        Enables Azure Active Directory authentication (Easy Auth) on the Web App.

        This configuration will require users to log in with an Azure AD account
        before they can access the application.

        Args:
            app_name (str): The name of the Web App to secure.

        Returns:
            bool: True if authentication was enabled successfully, False otherwise.
        """
        logger.info(f"🚀 Enabling Azure AD Authentication for Web App '{app_name}'...")

        # Note: For a fully automated setup, you would first create an App Registration
        # in Azure AD using the Microsoft Graph API to get a client_id.
        # Then you would pass that client_id here.
        # For this IaC script, we configure App Service to use "Express" mode,
        # which automatically creates the App Registration for us. This is a common and convenient approach.

        auth_settings = SiteAuthSettings(
            enabled=True,
            unauthenticated_client_action="RedirectToLoginPage",  # Redirect unauthenticated users to login
            default_provider="AzureActiveDirectory",
            # Configure Azure AD Provider
            aad_client_id=None,  # Set to None for Express management mode
            aad_client_secret=None,
            issuer="https://sts.windows.net/" + os.getenv("AZURE_TENANT_ID") + "/",
            # Token settings for enterprise scenarios
            token_store_enabled=True,
            allowed_external_redirect_urls=[],
            # Other providers can be configured here if needed (e.g., Google, Facebook)
            google_client_id=None,
            facebook_app_id=None,
            twitter_consumer_key=None,
            microsoft_account_client_id=None,
        )

        try:
            self.web_client.web_apps.update_auth_settings(
                resource_group_name=self.resource_group_name,
                name=app_name,
                site_auth_settings=auth_settings,
            )
            logger.info(
                f"✅ Successfully enabled Azure AD authentication for '{app_name}'."
            )
            logger.info(
                "   All unauthenticated traffic will now be redirected to the Azure AD login page."
            )
            return True

        except HttpResponseError as e:
            logger.error(f"❌ Failed to enable Azure AD authentication: {e.message}")
            if "is not available in this region" in str(e):
                logger.error(
                    "   Please ensure the App Service Plan SKU supports this feature."
                )
            return False
        except Exception as e:
            logger.error(f"❌ An unexpected error occurred during auth setup: {e}")
            return False


def main():
    """
    Main execution function to demonstrate Azure AD integration.
    """
    logger.info("=========================================================")
    logger.info("   Adaptive Mind - Azure AD Authentication Setup         ")
    logger.info("=========================================================")

    # This script depends on a pre-existing Web App.
    app_name_placeholder = "app-adaptive-mind-prod-xxxxxxxx"  # Placeholder
    logger.info(
        f"Simulating Azure AD integration for a pre-existing app: '{app_name_placeholder}'"
    )

    if not os.getenv("AZURE_TENANT_ID"):
        logger.error(
            "❌ AZURE_TENANT_ID environment variable is required for this script. Aborting."
        )
        return

    try:
        from azure_setup import AzureInfrastructureManager

        infra_manager = AzureInfrastructureManager()
        # Assume RG exists

        AzureADManager(
            credential=infra_manager.credential,
            subscription_id=infra_manager.subscription_id,
            resource_group_name=infra_manager.resource_group_name,
        )

        # In a real pipeline, we would get the app_name dynamically and call:
        # success = ad_manager.enable_azure_ad_authentication(actual_app_name)

        logger.info("--- Azure AD Integration Simulation ---")
        logger.info(
            "This script configures the 'Easy Auth' feature on the App Service."
        )
        logger.info("Key settings enabled:")
        logger.info("  - Authentication: ENABLED")
        logger.info("  - Action for unauthenticated users: RedirectToLoginPage")
        logger.info("  - Default Provider: AzureActiveDirectory (Entra ID)")
        logger.info("  - Management Mode: Express (auto-creates App Registration)")
        logger.info(
            "  - Token Store: ENABLED (for accessing APIs on behalf of the user)"
        )
        logger.info("---------------------------------------------")
        logger.info("✅ Azure AD integration script logic is complete.")
        logger.info(
            "ℹ️ When run against a real Web App, this will secure the entire application."
        )

    except Exception as e:
        logger.error(f"A critical error occurred: {e}")


if __name__ == "__main__":
    # To run this script fully, you would need:
    # 1. An Azure App Service already deployed.
    # 2. The AZURE_TENANT_ID environment variable set in your .env file.
    main()
