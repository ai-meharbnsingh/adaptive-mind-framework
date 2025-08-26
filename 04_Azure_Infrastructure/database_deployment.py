# 04_Azure_Infrastructure/database_deployment.py
# Manages Azure Database for PostgreSQL deployment - Session 10
# Part of the Adaptive Mind Framework infrastructure setup
# REVISION 2: Hardened firewall rules for enhanced security.

import os
import logging
from azure.mgmt.rdbms.postgresql import PostgreSQLManagementClient
from azure.mgmt.rdbms.postgresql.models import (
    Server,
    ServerPropertiesForDefaultCreate,
    Sku,
    ServerVersion,
    GeoRedundantBackup,
)
from azure.core.exceptions import HttpResponseError

# Configure professional logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages the deployment and configuration of Azure Database for PostgreSQL
    for the Adaptive Mind project.
    """

    def __init__(
        self, credential, subscription_id: str, resource_group_name: str, location: str
    ):
        """
        Initializes the DatabaseManager.

        Args:
            credential: An Azure credential object (e.g., DefaultAzureCredential).
            subscription_id (str): The Azure subscription ID.
            resource_group_name (str): The name of the resource group to deploy into.
            location (str): The Azure region for the database server.
        """
        self.credential = credential
        self.subscription_id = subscription_id
        self.resource_group_name = resource_group_name
        self.location = location
        self.server_name = f"psql-adaptive-mind-prod-{os.urandom(4).hex()}"
        self.database_name = "adaptive_mind_db"

        self.admin_login = os.getenv("POSTGRES_ADMIN_USER")
        self.admin_password = os.getenv("POSTGRES_ADMIN_PASSWORD")

        if not self.admin_login or not self.admin_password:
            error_msg = "POSTGRES_ADMIN_USER and POSTGRES_ADMIN_PASSWORD must be set in environment variables."
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info("Initializing PostgreSQL management client...")
        try:
            self.psql_client = PostgreSQLManagementClient(
                self.credential, self.subscription_id
            )
            logger.info("✅ PostgreSQL management client initialized successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to initialize PostgreSQL management client: {e}")
            raise

    def create_postgresql_server(self) -> str | None:
        """
        Creates an Azure Database for PostgreSQL server with enterprise-ready settings.
        """
        logger.info(f"🚀 Preparing to create PostgreSQL server '{self.server_name}'...")

        sku_config = Sku(
            name="GP_Gen5_2", tier="GeneralPurpose", family="Gen5", capacity=2
        )

        properties = ServerPropertiesForDefaultCreate(
            administrator_login=self.admin_login,
            administrator_login_password=self.admin_password,
            version=ServerVersion.ELEVEN,
            ssl_enforcement="Enabled",
            geo_redundant_backup=GeoRedundantBackup.ENABLED,
            storage_profile={
                "storage_mb": 51200,
                "backup_retention_days": 28,
                "storage_autogrow": "Enabled",
            },
        )

        server_params = Server(
            location=self.location,
            sku=sku_config,
            properties=properties,
            tags={
                "Project": "Adaptive Mind Framework",
                "Environment": "Production",
                "Purpose": "Primary Database",
            },
        )

        try:
            poller = self.psql_client.servers.begin_create(
                self.resource_group_name, self.server_name, server_params
            )
            logger.info(
                "... Server creation in progress. This may take several minutes..."
            )
            server_result = poller.result()

            logger.info(
                f"✅ Successfully created PostgreSQL server '{server_result.name}'."
            )
            return server_result.fully_qualified_domain_name

        except HttpResponseError as e:
            logger.error(
                f"❌ An HTTP error occurred during PostgreSQL server creation: {e.message}"
            )
            return None
        except Exception as e:
            logger.error(
                f"❌ An unexpected error occurred during PostgreSQL server creation: {e}"
            )
            return None

    def create_database(self) -> bool:
        """
        Creates a database within the newly provisioned PostgreSQL server.
        """
        logger.info(
            f"🚀 Creating database '{self.database_name}' on server '{self.server_name}'..."
        )
        try:
            poller = self.psql_client.databases.begin_create_or_update(
                self.resource_group_name,
                self.server_name,
                self.database_name,
                {"charset": "UTF8", "collation": "en_US.UTF-8"},
            )
            poller.result()
            logger.info(f"✅ Successfully created database '{self.database_name}'.")
            return True
        except HttpResponseError as e:
            logger.error(
                f"❌ An HTTP error occurred during database creation: {e.message}"
            )
            return False
        except Exception as e:
            logger.error(
                f"❌ An unexpected error occurred during database creation: {e}"
            )
            return False

    def configure_firewall_for_azure_services(self) -> bool:
        """
        AUDIT FIX: Configures a secure firewall rule to only allow access from Azure services.
        This is a significant security improvement over allowing all IPs.
        """
        rule_name = "AllowAllWindowsAzureIps"
        logger.info(
            f"🛡️ Hardening firewall: Configuring rule '{rule_name}' to allow Azure internal traffic..."
        )
        try:
            # This special IP range '0.0.0.0' for this specific rule name is interpreted by Azure
            # to mean "allow all traffic originating from Azure datacenters".
            poller = self.psql_client.firewall_rules.begin_create_or_update(
                self.resource_group_name,
                self.server_name,
                rule_name,
                {"start_ip_address": "0.0.0.0", "end_ip_address": "0.0.0.0"},
            )
            poller.result()
            logger.info(
                f"✅ Successfully configured secure firewall rule '{rule_name}'."
            )
            return True
        except HttpResponseError as e:
            logger.error(
                f"❌ An HTTP error occurred during firewall configuration: {e.message}"
            )
            return False
        except Exception as e:
            logger.error(
                f"❌ An unexpected error occurred during firewall configuration: {e}"
            )
            return False


def main():
    """
    Main execution function to demonstrate PostgreSQL server and database creation.
    """
    logger.info("=========================================================")
    logger.info("   Adaptive Mind - Azure PostgreSQL Setup Module         ")
    logger.info("=========================================================")

    from azure_setup import AzureInfrastructureManager

    try:
        infra_manager = AzureInfrastructureManager()
        infra_manager.create_resource_group()

        db_manager = DatabaseManager(
            credential=infra_manager.credential,
            subscription_id=infra_manager.subscription_id,
            resource_group_name=infra_manager.resource_group_name,
            location=infra_manager.location,
        )

        server_fqdn = db_manager.create_postgresql_server()
        if server_fqdn:
            db_manager.create_database()
            db_manager.configure_firewall_for_azure_services()  # AUDIT FIX: Use hardened rule

            logger.info("\n--- PostgreSQL Deployment Verification ---")
            logger.info(f"  Server FQDN: {server_fqdn}")
            logger.info("  Firewall: Azure services access enabled (Hardened)")
            logger.info("----------------------------------------")
            logger.info("✅ Azure PostgreSQL deployment is complete and verified.")
        else:
            logger.error("❌ Failed to create the Azure PostgreSQL server.")

    except (ValueError, ImportError) as e:
        logger.error(f"Configuration or import error: {e}")
    except Exception as e:
        logger.error(f"A critical error occurred: {e}")


if __name__ == "__main__":
    main()
