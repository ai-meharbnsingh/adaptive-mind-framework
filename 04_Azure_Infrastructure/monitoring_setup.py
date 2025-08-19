# 04_Azure_Infrastructure/monitoring_setup.py
# Manages Azure Application Insights deployment and linking - Session 10
# Part of the Adaptive Mind Framework infrastructure setup

import os
import logging
from azure.identity import DefaultAzureCredential
from azure.mgmt.applicationinsights import ApplicationInsightsManagementClient
from azure.mgmt.web import WebSiteManagementClient
from azure.mgmt.applicationinsights.models import ApplicationInsightsComponent
from azure.core.exceptions import HttpResponseError

# Configure professional logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class MonitoringManager:
    """
    Manages the deployment of Azure Application Insights and links it to the Web App.
    """

    def __init__(self, credential, subscription_id: str, resource_group_name: str, location: str):
        """
        Initializes the MonitoringManager.

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
        self.app_insights_name = f"appi-adaptive-mind-prod-{os.urandom(4).hex()}"

        logger.info("Initializing Application Insights and Web Site management clients...")
        try:
            self.app_insights_client = ApplicationInsightsManagementClient(self.credential, self.subscription_id)
            self.web_client = WebSiteManagementClient(self.credential, self.subscription_id)  # Needed for linking
            logger.info("✅ Monitoring-related management clients initialized successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to initialize monitoring management clients: {e}")
            raise

    def create_app_insights(self) -> str | None:
        """
        Creates an Azure Application Insights component.

        Returns:
            str | None: The instrumentation key of the component if created, otherwise None.
        """
        logger.info(f"🚀 Preparing to create Application Insights component '{self.app_insights_name}'...")

        app_insights_params = ApplicationInsightsComponent(
            location=self.location,
            kind="web",  # Specifies that this is for a web application
            application_type="web",
            tags={
                "Project": "Adaptive Mind Framework",
                "Environment": "Production",
                "Purpose": "APM and Observability"
            }
        )

        try:
            component = self.app_insights_client.components.create_or_update(
                resource_group_name=self.resource_group_name,
                resource_name=self.app_insights_name,
                insight_properties=app_insights_params
            )
            logger.info(f"✅ Successfully created Application Insights component '{component.name}'.")
            logger.info(f"   Instrumentation Key: {component.instrumentation_key}")
            return component.instrumentation_key
        except HttpResponseError as e:
            logger.error(f"❌ An HTTP error occurred during App Insights creation: {e.message}")
            return None
        except Exception as e:
            logger.error(f"❌ An unexpected error occurred during App Insights creation: {e}")
            return None

    def link_app_insights_to_webapp(self, app_name: str, instrumentation_key: str) -> bool:
        """
        Links the Application Insights component to an existing Web App by updating its settings.

        Args:
            app_name (str): The name of the Web App to link to.
            instrumentation_key (str): The instrumentation key from the App Insights component.

        Returns:
            bool: True if the linking was successful, False otherwise.
        """
        logger.info(f"🔗 Linking Application Insights to Web App '{app_name}'...")

        try:
            # Get the current application settings
            app_settings = self.web_client.web_apps.list_application_settings(
                self.resource_group_name,
                app_name
            ).properties

            # Add or update the Application Insights key
            # This specific key name enables automatic deep instrumentation in App Service.
            app_settings["APPINSIGHTS_INSTRUMENTATIONKEY"] = instrumentation_key

            # Update the settings on the web app
            self.web_client.web_apps.update_application_settings(
                self.resource_group_name,
                app_name,
                {"properties": app_settings}
            )

            logger.info(f"✅ Successfully linked App Insights to '{app_name}'. The app will restart to apply settings.")
            return True

        except HttpResponseError as e:
            logger.error(f"❌ An HTTP error occurred while linking App Insights: {e.message}")
            return False
        except Exception as e:
            logger.error(f"❌ An unexpected error occurred while linking App Insights: {e}")
            return False


def main():
    """
    Main execution function to demonstrate Application Insights setup and linking.
    """
    logger.info("=========================================================")
    logger.info("   Adaptive Mind - Azure Application Insights Setup      ")
    logger.info("=========================================================")

    # This main function simulates the full orchestration
    from azure_setup import AzureInfrastructureManager
    from container_registry_setup import ContainerRegistryManager
    from app_service_config import AppServiceManager

    try:
        # Run prerequisite steps to ensure the web app exists
        infra_manager = AzureInfrastructureManager()
        infra_manager.create_resource_group()

        acr_manager = ContainerRegistryManager(infra_manager.credential, infra_manager.subscription_id,
                                               infra_manager.resource_group_name, infra_manager.location)
        login_server = acr_manager.create_container_registry()
        acr_creds = acr_manager.get_registry_credentials()

        app_service_manager = AppServiceManager(infra_manager.credential, infra_manager.subscription_id,
                                                infra_manager.resource_group_name, infra_manager.location)
        plan_id = app_service_manager.create_app_service_plan()
        app_hostname = app_service_manager.create_web_app(plan_id, login_server, acr_creds['username'],
                                                          acr_creds['password'])

        if not app_hostname:
            logger.error("❌ Prerequisite failed: Web App not available. Aborting monitoring setup.")
            return

        # Now, set up and link Application Insights
        monitor_manager = MonitoringManager(
            credential=infra_manager.credential,
            subscription_id=infra_manager.subscription_id,
            resource_group_name=infra_manager.resource_group_name,
            location=infra_manager.location
        )

        instrumentation_key = monitor_manager.create_app_insights()

        if instrumentation_key:
            link_success = monitor_manager.link_app_insights_to_webapp(
                app_service_manager.app_name,
                instrumentation_key
            )

            if link_success:
                logger.info("\n--- Application Insights Verification ---")
                logger.info(f"  Component Name: {monitor_manager.app_insights_name}")
                logger.info(f"  Linked to Web App: {app_service_manager.app_name}")
                logger.info("  Action: APPINSIGHTS_INSTRUMENTATIONKEY has been set.")
                logger.info("  Result: Auto-instrumentation for performance and errors is now enabled.")
                logger.info("-----------------------------------------")
                logger.info("✅ Azure Application Insights setup and linking is complete.")

    except (ValueError, ImportError) as e:
        logger.error(f"Configuration or import error: {e}")
    except Exception as e:
        logger.error(f"A critical error occurred: {e}")


if __name__ == "__main__":
    # To run this script, you will need:
    # 1. All prerequisites from previous scripts.
    # 2. pip install azure-mgmt-applicationinsights

    main()