# -*- coding: utf-8 -*-
"""Deployments controller."""
import sys
from datetime import datetime

from projects import models, schemas
from projects.controllers.deployments.runs import RunController
from projects.controllers.experiments import ExperimentController
from projects.controllers.operators import OperatorController
from projects.controllers.templates import TemplateController
from projects.controllers.utils import uuid_alpha
from projects.exceptions import BadRequest, NotFound
from projects.kfp.deployments import get_deployment_runs, list_deployments_runs
from projects.kfp.monitorings import undeploy_monitoring

NOT_FOUND = NotFound("The specified deployment does not exist")


class DeploymentController:
    def __init__(self, session, background_tasks=None):
        self.session = session
        self.experiment_controller = ExperimentController(session)
        self.operator_controller = OperatorController(session)
        self.run_controller = RunController(session)
        self.template_controller = TemplateController(session)
        self.background_tasks = background_tasks

    def raise_if_deployment_does_not_exist(self, deployment_id: str):
        """
        Raises an exception if the specified deployment does not exist.

        Parameters
        ----------
        deployment_id : str

        Raises
        ------
        NotFound
        """
        exists = self.session.query(models.Deployment.uuid) \
            .filter_by(uuid=deployment_id) \
            .scalar() is not None

        if not exists:
            raise NOT_FOUND

    def list_deployments(self, project_id: str):
        """
        Lists all deployments under a project.

        Parameters
        ----------
        project_id: str

        Returns
        -------
        projects.schemas.deployment.DeploymentList
        """
        deployments = self.session.query(models.Deployment) \
            .filter_by(project_id=project_id) \
            .order_by(models.Deployment.position.asc()) \
            .all()

        deployments = schemas.DeploymentList.from_orm(deployments, len(deployments))

        deployment_runs = {}
        for deployment_run in list_deployments_runs():
            deployment_id = deployment_run["deploymentId"]
            if deployment_id not in deployment_runs:
                deployment_runs[deployment_id] = deployment_run

        for deployment in deployments.deployments:
            if deployment.uuid in deployment_runs:
                deployment_run = deployment_runs[deployment.uuid]
                deployment.deployed_at = deployment_run["createdAt"]
                deployment.status = deployment_run["status"]
                deployment.url = deployment_run["url"]

        return deployments

    def create_deployment(self, deployment: schemas.DeploymentCreate, project_id: str):
        """
        Creates new deployments in our database and adjusts the position of others.

        Parameters
        ----------
        deployment : DeploymentCreate
        project_id : str

        Returns
        -------
        projects.schemas.deployment.Deployment

        Raises
        ------
        NotFound
            When project_id does not exist.
        BadRequest
            When any experiment does not exist.
        """
        # ^ is xor operator. it's equivalent to (a and not b) or (not a and b)
        if not bool(deployment.experiments) ^ bool(deployment.template_id):
            raise BadRequest("either experiments or templateId is required")

        if deployment.template_id:
            return self.create_deployment_from_template(
                template_id=deployment.template_id,
                project_id=project_id
            )

        experiments_dict = {e.uuid: e for e in self.session.query(models.Experiment).filter_by(project_id=project_id)}

        for experiment_id in deployment.experiments:
            if experiment_id not in experiments_dict:
                raise BadRequest("some experiments do not exist")

        deployments = []

        for experiment_id in deployment.experiments:
            experiment = experiments_dict[experiment_id]
            deployment = models.Deployment(uuid=uuid_alpha(),
                                           experiment_id=experiment_id,
                                           name=experiment.name,
                                           project_id=project_id)
            self.session.add(deployment)
            self.session.flush()

            deployments.append(deployment)

            self.copy_operators(
                project_id=project_id,
                experiment_id=experiment_id,
                deployment_id=deployment.uuid
            )

            self.fix_positions(project_id=project_id,
                               deployment_id=deployment.uuid,
                               new_position=sys.maxsize)  # will add to end of list

        # Temporary: also run deployment (while web-ui isn't ready)
        for deployment in deployments:
            self.run_controller.create_run(project_id=project_id,
                                           deployment_id=deployment.uuid)

        self.session.commit()
        self.session.refresh(deployment)
        return schemas.Deployment.from_orm(deployment)

    def get_deployment(self, project_id: str, deployment_id: str):
        """
        Details a deployment from our database.

        Parameters
        ----------
        project_id : str
        deployment_id : str

        Returns
        -------
        projects.schemas.deployment.Deployment

        Raises
        ------
        NotFound
            When deployment_id does not exist.
        """
        deployment = self.session.query(models.Deployment).get(deployment_id)
        if deployment is None:
            raise NOT_FOUND

        deployment = schemas.Deployment.from_orm(deployment)

        deployment_runs = get_deployment_runs(deployment_id)

        if not deployment_runs:
            deployment.deployed_at = deployment_runs["createdAt"]
            deployment.status = deployment_runs["status"]
            deployment.url = deployment_runs["url"]

        return deployment

    def update_deployment(self, deployment: schemas.DeploymentUpdate, project_id: str, deployment_id: str):
        """
        Updates a deployment in our database and adjusts the position of others.

        Parameters
        ----------
        deployment : projects.schemas.deployment.DeploymentUpdate
        project_id : str
        deployment_id : str

        Returns
        -------
        projects.schemas.deployment.Deployment

        Raises
        ------
        NotFound
            When deployment_id does not exist.
        BadRequest
            When name is already the name of another deployment.
        """
        self.raise_if_deployment_does_not_exist(deployment_id)

        stored_deployment = self.session.query(models.deployment.Deployment) \
            .filter(models.deployment.Deployment.project_id == project_id) \
            .filter_by(name=deployment.name) \
            .first()
        if stored_deployment and stored_deployment.uuid != deployment_id:
            raise BadRequest("a deployment with that name already exists")

        update_data = deployment.dict(exclude_unset=True)
        update_data.update({"updated_at": datetime.utcnow()})

        self.session.query(models.Deployment).filter_by(uuid=deployment_id).update(update_data)

        if deployment.position:
            self.fix_positions(project_id=project_id,
                               deployment_id=deployment_id,
                               new_position=deployment.position)

        self.session.commit()

        deployment = self.session.query(models.Deployment).get(deployment_id)

        return schemas.Deployment.from_orm(deployment)

    def delete_deployment(self, project_id: str, deployment_id: str):
        """
        Delete a deployment in our database and in the object storage.

        Parameters
        ----------
        project_id: str
        deployment_id : str

        Raises
        ------
        NotFound
            When deployment_id does not exist.

        Returns
        -------
        projects.schemas.message.Message
        """
        deployment = self.session.query(models.Deployment).get(deployment_id)

        if deployment is None:
            raise NOT_FOUND

        # remove responses
        self.session.query(models.Response).filter(models.Response.deployment_id == deployment_id).delete()

        # remove operators
        self.session.query(models.Operator).filter(models.Operator.deployment_id == deployment_id).delete()

        # remove monitorings
        monitorings = self.session.query(models.Monitoring).filter(models.Monitoring.deployment_id == deployment_id)
        # Undeploy monitorings
        if monitorings:
            for monitoring in monitorings:
                self.background_tasks.add_task(
                    undeploy_monitoring,
                    monitoring_id=monitoring.uuid
                )

        # delete monitorings on database
        monitorings.delete()

        self.session.delete(deployment)

        self.fix_positions(project_id=project_id)

        self.session.commit()

        # Temporary: also delete run deployment (while web-ui isn't ready)
        self.run_controller = self.run_controller.terminate_run(
            project_id=project_id,
            deployment_id=deployment_id,
            run_id="latest"
        )

        return schemas.Message(message="Deployment deleted")

    def fix_positions(self, project_id: str, deployment_id=None, new_position=None):
        """
        Reorders the deployments in a project when a deployment is updated/deleted.

        Parameters
        ----------
        project_id : str
        deployment_id : str
        new_position : int
            The position where the experiment is shown.
        """
        other_deployments = self.session.query(models.Deployment) \
            .filter_by(project_id=project_id) \
            .filter(models.Deployment.uuid != deployment_id) \
            .order_by(models.Deployment.position.asc()) \
            .all()

        if deployment_id is not None:
            deployment = self.session.query(models.Deployment).get(deployment_id)
            other_deployments.insert(new_position, deployment)

        for index, deployment in enumerate(other_deployments):
            data = {"position": index}
            is_last = (index == len(other_deployments) - 1)
            # if deployment_id WAS NOT informed, then set the higher position as is_active=True
            if deployment_id is None and is_last:
                data["is_active"] = True
            # if deployment_id WAS informed, then set experiment.is_active=True
            elif deployment_id is not None and deployment_id == deployment.uuid:
                data["is_active"] = True
            else:
                data["is_active"] = False

            self.session.query(models.Deployment).filter_by(uuid=deployment.uuid).update(data)

    def copy_operators(self, project_id: str, experiment_id: str, deployment_id: str):
        """
        Copies the operators from an experiment to a deployment.
        Creates new uuids and don't keep the experiment_id relationship.

        Parameters
        ----------
        project_id : str
        experiment_id : str
        deployment_id : str
        """
        stored_experiment = self.session.query(models.Experiment).get(experiment_id)

        # Creates a dict to map source operator_id to its copy operator_id.
        # This map will be used to build the dependencies using new operator_ids
        copies_map = {}

        for stored_operator in stored_experiment.operators:
            operator = schemas.OperatorCreate(
                task_id=stored_operator.task_id,
                deployment_id=deployment_id,
                parameters=stored_operator.parameters,
                position_x=stored_operator.position_x,
                position_y=stored_operator.position_y,
            )

            operator = self.operator_controller.create_operator(
                operator=operator,
                project_id=project_id,
                deployment_id=deployment_id
            )

            copies_map[stored_operator.uuid] = {
                "copy_uuid": operator.uuid,
                "dependencies": stored_operator.dependencies,
            }

        # sets dependencies on new operators
        for _, value in copies_map.items():
            operator = schemas.OperatorUpdate(
                dependencies=[copies_map[d]["copy_uuid"] for d in value["dependencies"]],
            )
            self.operator_controller.update_operator(project_id=project_id,
                                                     deployment_id=deployment_id,
                                                     operator_id=value["copy_uuid"],
                                                     operator=operator)

    def create_deployment_from_template(self, template_id: str, project_id: str):
        """
        Creates the operators of deployment using a template.

        Parameters
        ----------
        template_id : str
        project_id : str
        """
        template = self.template_controller.get_template(template_id)
        deployment = models.Deployment(uuid=uuid_alpha(),
                                       name=template.name,
                                       project_id=project_id)
        self.session.add(deployment)
        self.session.flush()

        # save the operators created to get the created_uuid to use on dependencies
        operators_created = []
        for task in template.tasks:
            dependencies = []
            task_dependencies = task["dependencies"]
            if len(task_dependencies) > 0:
                for d in task_dependencies:
                    op_created = next((o for o in operators_created if o["uuid"] == d), None)
                    dependencies.append(op_created["created_uuid"])

            operator_id = uuid_alpha()
            objects = [
                models.Operator(
                    uuid=operator_id,
                    deployment_id=deployment.uuid,
                    task_id=task["task_id"],
                    dependencies=dependencies,
                    position_x=task["position_x"],
                    position_y=task["position_y"],
                )
            ]
            self.session.bulk_save_objects(objects)
            task["created_uuid"] = operator_id
            operators_created.append(task)

        self.session.commit()
        self.session.refresh(deployment)

        return schemas.Deployment.from_orm(deployment)
