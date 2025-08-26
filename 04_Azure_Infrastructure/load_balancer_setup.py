# 04_Azure_Infrastructure/load_balancer_setup.py
# Manages Azure Load Balancer for high availability - Session 10
# Part of the Adaptive Mind Framework infrastructure setup

import logging
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.network.models import (
    PublicIPAddress,
    LoadBalancer,
    FrontendIPConfiguration,
    BackendAddressPool,
    HealthProbe,
    LoadBalancingRule,
    TransportProtocol,
    ProbeProtocol,
)
from azure.core.exceptions import HttpResponseError

# Configure professional logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-m-d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class HighAvailabilityManager:
    """
    Manages the deployment of Azure Load Balancer for high availability and scalability.
    """

    def __init__(
        self, credential, subscription_id: str, resource_group_name: str, location: str
    ):
        """
        Initializes the HighAvailabilityManager.

        Args:
            credential: An Azure credential object (e.g., DefaultAzureCredential).
            subscription_id (str): The Azure subscription ID.
            resource_group_name (str): The name of the resource group to deploy into.
            location (str): The Azure region for the resources.
        """
        self.credential = credential
        self.subscription_id = subscription_id
        self.resource_group_name = resource_group_name
        self.location = location
        self.public_ip_name = "pip-adaptive-mind-prod"
        self.lb_name = "lb-adaptive-mind-prod"

        logger.info("Initializing Network management client...")
        try:
            self.network_client = NetworkManagementClient(
                self.credential, self.subscription_id
            )
            logger.info("✅ Network management client initialized successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Network management client: {e}")
            raise

    def create_public_ip(self) -> PublicIPAddress:
        """
        Creates a standard, static public IP address for the Load Balancer.

        Returns:
            PublicIPAddress: The created Public IP Address object.
        """
        logger.info(f"🚀 Creating Public IP Address '{self.public_ip_name}'...")
        try:
            poller = self.network_client.public_ip_addresses.begin_create_or_update(
                self.resource_group_name,
                self.public_ip_name,
                PublicIPAddress(
                    location=self.location,
                    sku={"name": "Standard"},
                    public_ip_allocation_method="Static",
                    tags={
                        "Project": "Adaptive Mind Framework",
                        "Environment": "Production",
                    },
                ),
            )
            ip_address = poller.result()
            logger.info(
                f"✅ Successfully created Public IP Address '{ip_address.name}' with IP: {ip_address.ip_address}"
            )
            return ip_address
        except HttpResponseError as e:
            logger.error(f"❌ Failed to create Public IP Address: {e.message}")
            raise

    def create_load_balancer(self, public_ip_address: PublicIPAddress) -> LoadBalancer:
        """
        Creates an Azure Load Balancer.

        Args:
            public_ip_address (PublicIPAddress): The public IP object to associate with the LB.

        Returns:
            LoadBalancer: The created Load Balancer object.
        """
        logger.info(f"🚀 Creating Load Balancer '{self.lb_name}'...")
        try:
            frontend_ip_config = FrontendIPConfiguration(
                name="loadBalancerFrontend", public_ip_address=public_ip_address
            )

            backend_pool = BackendAddressPool(name="backendAddressPool")

            # Health probe to check the health of backend instances on port 443 (HTTPS)
            health_probe = HealthProbe(
                name="healthProbe",
                protocol=ProbeProtocol.TCP,
                port=443,
                interval_in_seconds=5,
                number_of_probes=2,
            )

            # Load balancing rule to route HTTPS traffic from port 443 to the backend pool
            lb_rule = LoadBalancingRule(
                name="httpsRule",
                protocol=TransportProtocol.TCP,
                frontend_port=443,
                backend_port=443,
                frontend_ip_configuration=frontend_ip_config,
                backend_address_pool=backend_pool,
                probe=health_probe,
                enable_floating_ip=False,
            )

            lb_params = LoadBalancer(
                location=self.location,
                sku={"name": "Standard"},
                frontend_ip_configurations=[frontend_ip_config],
                backend_address_pools=[backend_pool],
                probes=[health_probe],
                load_balancing_rules=[lb_rule],
                tags={
                    "Project": "Adaptive Mind Framework",
                    "Environment": "Production",
                },
            )

            poller = self.network_client.load_balancers.begin_create_or_update(
                self.resource_group_name, self.lb_name, lb_params
            )
            load_balancer = poller.result()
            logger.info(
                f"✅ Successfully created Load Balancer '{load_balancer.name}'."
            )
            return load_balancer
        except HttpResponseError as e:
            logger.error(f"❌ Failed to create Load Balancer: {e.message}")
            raise


def main():
    """
    Main execution function to demonstrate Load Balancer setup.
    """
    logger.info("=========================================================")
    logger.info("   Adaptive Mind - Azure Load Balancer Setup             ")
    logger.info("=========================================================")

    from azure_setup import AzureInfrastructureManager

    try:
        infra_manager = AzureInfrastructureManager()
        if not infra_manager.create_resource_group():
            logger.error("❌ Prerequisite failed: Resource group not available.")
            return

        ha_manager = HighAvailabilityManager(
            credential=infra_manager.credential,
            subscription_id=infra_manager.subscription_id,
            resource_group_name=infra_manager.resource_group_name,
            location=infra_manager.location,
        )

        public_ip = ha_manager.create_public_ip()
        load_balancer = ha_manager.create_load_balancer(public_ip)

        logger.info("\n--- Load Balancer Verification ---")
        logger.info(f"  Load Balancer Name: {load_balancer.name}")
        logger.info(f"  Public IP Address: {public_ip.ip_address}")
        logger.info("  SKU: Standard")
        logger.info("  Rule: Forwarding TCP port 443 (HTTPS)")
        logger.info("  Health Probe: TCP on port 443, every 5 seconds")
        logger.info("----------------------------------")
        logger.info("✅ Azure Load Balancer setup is complete.")
        logger.info(
            "ℹ️ Next step will be to link the App Service backend pool to this load balancer."
        )

    except (ValueError, ImportError) as e:
        logger.error(f"Configuration or import error: {e}")
    except Exception as e:
        logger.error(f"A critical error occurred: {e}")


if __name__ == "__main__":
    # To run this script, you will need:
    # 1. All prerequisites from previous scripts.
    # 2. pip install azure-mgmt-network

    main()
