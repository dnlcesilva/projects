# -*- coding: utf-8 -*-
"""Deployments Runs controller."""
from kubernetes import client
from kubernetes.client.rest import ApiException

from projects import models, schemas
from projects.controllers.monitorings import MonitoringController
from projects.exceptions import BadRequest, NotFound
from projects.kfp import KF_PIPELINES_NAMESPACE, kfp_client
from projects.kfp import runs as kfp_runs
from projects.kfp.deployments import get_deployment_runs
from projects.kfp.monitorings import deploy_monitoring
from projects.kfp.pipeline import undeploy_pipeline
from projects.kubernetes.kube_config import load_kube_config


NOT_FOUND = NotFound("The specified run does not exist")


class RunController:
    def __init__(self, session, background_tasks=None):
        self.session = session
        self.background_tasks = background_tasks
        self.monitoring_controller = MonitoringController(session)

    def raise_if_run_does_not_exist(self, run_id: str, deployment_id: str):
        """
        Raises an exception if the specified run does not exist.

        Parameters
        ----------
        run_id : str
        deployment_id : str

        Raises
        ------
        NotFound
        """
        try:
            kfp_runs.get_run(experiment_id=deployment_id,
                             run_id=run_id)
        except (ApiException, ValueError):
            raise NOT_FOUND

    def list_runs(self, project_id: str, deployment_id: str):
        """
        Lists all runs under a deployment.

        Parameters
        ----------
        project_id : str
        deployment_id : str

        Returns
        -------
        projects.schemas.run.RunList
        """
        runs = kfp_runs.list_runs(experiment_id=deployment_id)
        return schemas.RunList.from_orm(runs, len(runs))

    def create_run(self, project_id: str, deployment_id: str):
        """
        Starts a new run in Kubeflow Pipelines.

        Parameters
        ----------
        project_id : str
        deployment_id : str

        Returns
        -------
        projects.schemas.run.Run

        Raises
        ------
        NotFound
            When any of project_id, or deployment_id does not exist.
        """
        deployment = self.session.query(models.Deployment).get(deployment_id)

        if deployment is None:
            raise NotFound("The specified deployment does not exist")

        # Removes operators that don't have a deployment_notebook (eg. Upload de Dados).
        # Then, fix dependencies in their children.
        operators = self.remove_non_deployable_operators(deployment.operators)

        try:
            run = kfp_runs.start_run(operators=operators,
                                     project_id=deployment.project_id,
                                     experiment_id=deployment.experiment_id,
                                     deployment_id=deployment_id,
                                     deployment_name=deployment.name)
        except ValueError as e:
            raise BadRequest(str(e))

        # Deploy monitoring tasks
        monitorings = self.monitoring_controller.list_monitorings(project_id=project_id,
                                                                  deployment_id=deployment_id).monitorings
        if monitorings:
            for monitoring in monitorings:
                self.background_tasks.add_task(
                    deploy_monitoring,
                    deployment_id=deployment_id,
                    experiment_id=deployment.experiment_id,
                    run_id=run["uuid"],
                    task_id=monitoring.task_id,
                    monitoring_id=monitoring.uuid
                )

        update_data = {"status": "Pending"}
        self.session.query(models.Operator) \
            .filter_by(deployment_id=deployment_id) \
            .update(update_data)
        self.session.commit()

        run["deploymentId"] = deployment_id
        return run

    def get_run(self, project_id: str, deployment_id: str, run_id: str):
        """
        Details a run in Kubeflow Pipelines.

        Parameters
        ----------
        project_id : str
        deployment_id : str
        run_id : str

        Returns
        -------
        projects.schemas.run.Run

        Raises
        ------
        NotFound
            When any of project_id, deployment_id, or run_id does not exist.
        """
        run = get_deployment_runs(deployment_id)

        return run

    def terminate_run(self, project_id, deployment_id, run_id):
        """
        Terminates a run in Kubeflow Pipelines.

        Parameters
        ----------
        project_id : str
        deployment_id : str
        run_id : str

        Returns
        -------
        projects.schemas.message.Message

        Raises
        ------
        NotFound
            When any of project_id, deployment_id, or run_id does not exist.
        """
        load_kube_config()
        api = client.CustomObjectsApi()
        custom_objects = api.list_namespaced_custom_object(
            "machinelearning.seldon.io",
            "v1alpha2",
            KF_PIPELINES_NAMESPACE,
            "seldondeployments"
        )
        deployments_objects = custom_objects["items"]

        if deployments_objects:
            for deployment in deployments_objects:
                if deployment["metadata"]["name"] == deployment_id:
                    undeploy_pipeline(deployment)

        deployment_run = get_deployment_runs(deployment_id)

        if not deployment_run:
            raise NotFound("Deployment run does not exist.")

        kfp_client().runs.delete_run(deployment_run["runId"])

        return schemas.Message(message="Deployment deleted")

    def remove_non_deployable_operators(self, operators):
        """
        Removes operators that are not part of the deployment pipeline.

        Parameters
        ----------
        operators : list
            Original pipeline operators.

        Returns
        -------
        list
            A list of all deployable operators.

        Notes
        -----
        If the non-deployable operator is dependent on another operator, it will be
        removed from that operator's dependency list.
        """
        deployable_operators = [o for o in operators if o.task.deployment_notebook_path is not None]
        non_deployable_operators = self.get_non_deployable_operators(operators, deployable_operators)

        for operator in deployable_operators:
            dependencies = set(operator.dependencies)
            operator.dependencies = list(dependencies - set(non_deployable_operators))

        return deployable_operators

    def get_non_deployable_operators(self, operators, deployable_operators):
        """
        Get all non-deployable operators from a deployment run.

        Parameters
        ----------
        operators : list
        deployable_operators : list

        Returns
        -------
        list
            A list of non deployable operators.
        """
        non_deployable_operators = []
        for operator in operators:
            if operator.task.deployment_notebook_path is None:
                # checks if the non-deployable operator has dependency
                if operator.dependencies:
                    dependency = operator.dependencies

                    # looks for who has the non-deployable operator as dependency
                    # and assign the dependency of the non-deployable operator to this operator
                    for op in deployable_operators:
                        if operator.uuid in op.dependencies:
                            op.dependencies = dependency

                non_deployable_operators.append(operator.uuid)

        return non_deployable_operators
