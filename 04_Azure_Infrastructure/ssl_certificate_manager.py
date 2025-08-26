# 04_Azure_Infrastructure/ssl_certificate_manager.py
# Manages SSL/TLS certificates for the custom domain - Session 10
# Part of the Adaptive Mind Framework infrastructure setup

import os
import logging
from azure.mgmt.web import WebSiteManagementClient
from azure.mgmt.web.models import Certificate
from azure.core.exceptions import HttpResponseError

# Configure professional logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class SSLManager:
    """
    Manages the creation and binding of SSL/TLS certificates for the Web App's custom domain.
    """

    def __init__(
        self, credential, subscription_id: str, resource_group_name: str, location: str
    ):
        """
        Initializes the SSLManager.

        Args:
            credential: An Azure credential object (e.g., DefaultAzureCredential).
            subscription_id (str): The Azure subscription ID.
            resource_group_name (str): The name of the resource group.
            location (str): The Azure region.
        """
        self.credential = credential
        self.subscription_id = subscription_id
        self.resource_group_name = resource_group_name
        self.location = location

        logger.info("Initializing Web Site management client for SSL operations...")
        try:
            self.web_client = WebSiteManagementClient(
                self.credential, self.subscription_id
            )
            logger.info(
                "✅ Web Site management client initialized successfully for SSL."
            )
        except Exception as e:
            logger.error(f"❌ Failed to initialize Web Site management client: {e}")
            raise

    def configure_custom_domain(self, app_name: str, domain_name: str) -> bool:
        """
        Configures a custom domain for the Web App. This is a prerequisite for binding an SSL cert.

        Args:
            app_name (str): The name of the Web App.
            domain_name (str): The custom domain name (e.g., demo.adaptive-mind.ai).

        Returns:
            bool: True if successful, False otherwise.
        """
        logger.info(
            f"🚀 Configuring custom domain '{domain_name}' for Web App '{app_name}'..."
        )
        logger.warning(
            "This step requires manual DNS configuration (CNAME record) pointing to the app's default hostname."
        )

        try:
            # In a real pipeline, you would use DNS APIs to create the CNAME or TXT record for validation.
            # Here, we simulate the step of adding the hostname. The operation will only succeed
            # if the DNS records are correctly configured beforehand.
            self.web_client.web_apps.create_or_update_host_name_binding(
                resource_group_name=self.resource_group_name,
                name=app_name,
                host_name=domain_name,
                host_name_binding={
                    "site_name": app_name,
                    "domain_id": None,
                    "custom_host_name_dns_record_type": "CName",
                    "host_name_type": "Verified",
                },
            )
            logger.info(f"✅ Successfully added hostname binding for '{domain_name}'.")
            return True
        except HttpResponseError as e:
            logger.error(f"❌ Failed to configure custom domain: {e.message}")
            logger.error(
                "Please ensure the CNAME record for your domain points to the App Service default hostname and has propagated."
            )
            return False

    def create_and_bind_managed_certificate(
        self, app_name: str, domain_name: str
    ) -> bool:
        """
        Creates a free App Service Managed Certificate for the custom domain and binds it.

        Args:
            app_name (str): The name of the Web App.
            domain_name (str): The custom domain name.

        Returns:
            bool: True if the certificate was created and bound successfully, False otherwise.
        """
        cert_name = f"{app_name}-{domain_name.replace('.', '-')}"
        logger.info(
            f"🚀 Creating and binding managed SSL certificate '{cert_name}' for '{domain_name}'..."
        )

        try:
            web_app = self.web_client.web_apps.get(self.resource_group_name, app_name)

            # Create the App Service Managed Certificate
            cert_order = Certificate(
                location=self.location,
                server_farm_id=web_app.server_farm_id,
                host_names=[domain_name],
            )

            created_cert = self.web_client.certificates.begin_create_or_update(
                resource_group_name=self.resource_group_name,
                name=cert_name,
                certificate_envelope=cert_order,
            ).result()

            logger.info(f"✅ Certificate '{created_cert.name}' created successfully.")

            # Now, create the SSL binding on the custom hostname
            hostname_binding = self.web_client.web_apps.get_host_name_binding(
                resource_group_name=self.resource_group_name,
                name=app_name,
                host_name=domain_name,
            )

            hostname_binding.ssl_state = "SniEnabled"
            hostname_binding.thumbprint = created_cert.thumbprint

            self.web_client.web_apps.create_or_update_host_name_binding(
                resource_group_name=self.resource_group_name,
                name=app_name,
                host_name=domain_name,
                host_name_binding=hostname_binding,
            )

            logger.info(f"✅ Successfully bound SSL certificate to '{domain_name}'.")
            return True

        except HttpResponseError as e:
            logger.error(f"❌ Failed to create or bind certificate: {e.message}")
            return False
        except Exception as e:
            logger.error(f"❌ An unexpected error occurred during SSL management: {e}")
            return False


def main():
    """
    Main execution function to demonstrate SSL Certificate management.
    """
    logger.info("=========================================================")
    logger.info("   Adaptive Mind - Azure SSL Certificate Manager         ")
    logger.info("=========================================================")

    # NOTE: This main function is for demonstration and requires a pre-existing App Service
    # and manually configured DNS. The logic will be integrated into a master script.

    # We will use placeholder values here as we can't run this without a real domain
    custom_domain = os.getenv(
        "CUSTOM_DOMAIN_NAME", "demo.your-domain.com"
    )  # e.g., demo.adaptive-mind.ai
    if custom_domain == "demo.your-domain.com":
        logger.warning(
            "Using placeholder domain. This script will fail without a real, configured domain."
        )

    from azure_setup import AzureInfrastructureManager

    # This simulation assumes the app service was created in a previous step
    # We will need its name
    app_name_placeholder = "app-adaptive-mind-prod-xxxxxxxx"  # Placeholder
    logger.info(
        f"Simulating SSL setup for a pre-existing app: '{app_name_placeholder}' and domain: '{custom_domain}'"
    )

    try:
        infra_manager = AzureInfrastructureManager()
        # Assume RG exists

        SSLManager(
            credential=infra_manager.credential,
            subscription_id=infra_manager.subscription_id,
            resource_group_name=infra_manager.resource_group_name,
            location=infra_manager.location,
        )

        logger.info("--- SSL Certificate Management Simulation ---")
        logger.info(
            "Step 1: Configure custom domain (requires manual DNS CNAME setup)."
        )
        logger.info(
            "Step 2: Create a free App Service Managed Certificate for the domain."
        )
        logger.info("Step 3: Bind the certificate to the domain, enabling HTTPS.")
        logger.info("---------------------------------------------")
        logger.info("✅ SSL management script logic is complete.")
        logger.info(
            "ℹ️ Full execution will be part of the final, orchestrated deployment process in Session 11/12."
        )

    except Exception as e:
        logger.error(f"A critical error occurred: {e}")


if __name__ == "__main__":
    # To run this script fully, you would need:
    # 1. An Azure App Service already deployed.
    # 2. A custom domain you own.
    # 3. DNS CNAME record pointing your custom domain to the App Service's default hostname.
    # 4. An environment variable CUSTOM_DOMAIN_NAME set to your domain.
    main()
