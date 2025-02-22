# -*- coding: utf-8 -*-
from json import dumps
from unittest import TestCase

from fastapi.testclient import TestClient

from projects.api.main import app
from projects.controllers.utils import uuid_alpha
from projects.database import engine
from projects.object_storage import BUCKET_NAME

TEST_CLIENT = TestClient(app)

EXPERIMENT_ID = str(uuid_alpha())
NAME = "foo"
POSITION = 0
EXPERIMENT_ID_2 = str(uuid_alpha())
EXPERIMENT_ID_3 = str(uuid_alpha())
EXPERIMENT_ID_4 = str(uuid_alpha())
NAME_2 = "foo 2"
NAME_3 = "foo 3"
NAME_4 = "foo 4"
POSITION_2 = 1
POSITION_3 = 2
POSITION_4 = 3
PROJECT_ID = str(uuid_alpha())
TEMPLATE_ID = str(uuid_alpha())
TASK_ID = str(uuid_alpha())
TASK_ID_2 = str(uuid_alpha())
TASK_ID_3 = str(uuid_alpha())
TASK_ID_4 = str(uuid_alpha())
OPERATOR_ID = str(uuid_alpha())
OPERATOR_ID_2 = str(uuid_alpha())
OPERATOR_ID_3 = str(uuid_alpha())
OPERATOR_ID_4 = str(uuid_alpha())
OPERATOR_ID_5 = str(uuid_alpha())
DEPENDENCY_ID = str(uuid_alpha())
IS_ACTIVE = True
PARAMETERS = {"coef": 0.1}
PARAMETERS_JSON = dumps(PARAMETERS)
PARAMETERS_JSON_2 = dumps({})
DESCRIPTION = "long foo"
IMAGE = "platiagro/platiagro-experiment-image:0.2.0"
COMMANDS = None
ARGUMENTS = None
TAGS = ["PREDICTOR"]
TAGS_2 = ["DATASETS"]
TAGS_JSON = dumps(TAGS)
TAGS_JSON_2 = dumps(TAGS_2)
TASKS_JSON = dumps([
    {
        "uuid": OPERATOR_ID,
        "position_x": 0.0,
        "position_y": 0.0,
        "task_id": TASK_ID,
        "dependencies": []
    },
    {
        "uuid": OPERATOR_ID_2,
        "position_x": 200.0,
        "position_y": 0.0,
        "task_id": TASK_ID_2,
        "dependencies": [OPERATOR_ID]
    },
])
EXPERIMENT_NOTEBOOK_PATH = f"minio://{BUCKET_NAME}/tasks/{TASK_ID}/Experiment.ipynb"
DEPLOYMENT_NOTEBOOK_PATH = f"minio://{BUCKET_NAME}/tasks/{TASK_ID}/Deployment.ipynb"
EXPERIMENT_NOTEBOOK_PATH_2 = {}
CREATED_AT = "2000-01-01 00:00:00"
CREATED_AT_ISO = "2000-01-01T00:00:00"
UPDATED_AT = "2000-01-01 00:00:00"
UPDATED_AT_ISO = "2000-01-01T00:00:00"
NAME_COPYFROM = "test copyFrom"

DEPENDENCIES_EMPTY = []
DEPENDENCIES_EMPTY_JSON = dumps(DEPENDENCIES_EMPTY)
DEPENDENCIES_OP_ID = [OPERATOR_ID]
DEPENDENCIES_OP_ID_JSON = dumps(DEPENDENCIES_OP_ID)


class TestExperiments(TestCase):
    def setUp(self):
        self.maxDiff = None

        conn = engine.connect()
        text = (
            f"INSERT INTO tasks (uuid, name, description, image, commands, arguments, tags, parameters, experiment_notebook_path, deployment_notebook_path, is_default, created_at, updated_at) "
            f"VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )
        conn.execute(text, (TASK_ID, NAME, DESCRIPTION, IMAGE, None, None, TAGS_JSON, dumps(
            []), EXPERIMENT_NOTEBOOK_PATH, DEPLOYMENT_NOTEBOOK_PATH, 0, CREATED_AT, UPDATED_AT,))

        text = (
            f"INSERT INTO tasks (uuid, name, description, image, commands, arguments, tags, parameters, experiment_notebook_path, deployment_notebook_path, is_default, created_at, updated_at) "
            f"VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )
        conn.execute(text, (TASK_ID_2, NAME_2, DESCRIPTION, IMAGE, None, None, TAGS_JSON, dumps(
            []), EXPERIMENT_NOTEBOOK_PATH, DEPLOYMENT_NOTEBOOK_PATH, 0, CREATED_AT, UPDATED_AT,))

        text = (
            f"INSERT INTO tasks (uuid, name, description, image, commands, arguments, tags, parameters, experiment_notebook_path, deployment_notebook_path, is_default, created_at, updated_at) "
            f"VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )
        conn.execute(text, (TASK_ID_3, NAME_3, DESCRIPTION, IMAGE, None, None, TAGS_JSON_2, dumps(
            []), EXPERIMENT_NOTEBOOK_PATH, DEPLOYMENT_NOTEBOOK_PATH, 0, CREATED_AT, UPDATED_AT,))

        text = (
            f"INSERT INTO tasks (uuid, name, description, image, commands, arguments, tags, parameters, experiment_notebook_path, deployment_notebook_path, is_default, created_at, updated_at) "
            f"VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )
        conn.execute(text, (TASK_ID_4, NAME_4, DESCRIPTION, IMAGE, None, None, TAGS_JSON_2, dumps(
            []), EXPERIMENT_NOTEBOOK_PATH_2, DEPLOYMENT_NOTEBOOK_PATH, 0, CREATED_AT, UPDATED_AT,))

        text = (
            f"INSERT INTO projects (uuid, name, created_at, updated_at) "
            f"VALUES (%s, %s, %s, %s)"
        )
        conn.execute(text, (PROJECT_ID, NAME, CREATED_AT, UPDATED_AT,))

        text = (
            f"INSERT INTO experiments (uuid, name, project_id, position, is_active, created_at, updated_at) "
            f"VALUES (%s, %s, %s, %s, %s, %s, %s)"
        )
        conn.execute(text, (EXPERIMENT_ID, NAME, PROJECT_ID, POSITION, 1, CREATED_AT, UPDATED_AT,))

        text = (
            f"INSERT INTO experiments (uuid, name, project_id, position, is_active, created_at, updated_at) "
            f"VALUES (%s, %s, %s, %s, %s, %s, %s)"
        )
        conn.execute(text, (EXPERIMENT_ID_2, NAME_2, PROJECT_ID, POSITION_2, 1, CREATED_AT, UPDATED_AT,))

        text = (
            f"INSERT INTO experiments (uuid, name, project_id, position, is_active, created_at, updated_at) "
            f"VALUES (%s, %s, %s, %s, %s, %s, %s)"
        )
        conn.execute(text, (EXPERIMENT_ID_3, NAME_3, PROJECT_ID, POSITION_3, 1, CREATED_AT, UPDATED_AT,))

        text = (
            f"INSERT INTO experiments (uuid, name, project_id, position, is_active, created_at, updated_at) "
            f"VALUES (%s, %s, %s, %s, %s, %s, %s)"
        )
        conn.execute(text, (EXPERIMENT_ID_4, NAME_4, PROJECT_ID, POSITION_4, 1, CREATED_AT, UPDATED_AT,))

        text = (
            f"INSERT INTO operators (uuid, experiment_id, task_id, parameters, dependencies, created_at, updated_at) "
            f"VALUES (%s, %s, %s, %s, %s, %s, %s)"
        )
        conn.execute(text, (OPERATOR_ID, EXPERIMENT_ID, TASK_ID, PARAMETERS_JSON, DEPENDENCIES_EMPTY_JSON, CREATED_AT, UPDATED_AT,))

        text = (
            f"INSERT INTO operators (uuid, experiment_id, task_id, parameters, dependencies, created_at, updated_at) "
            f"VALUES (%s, %s, %s, %s, %s, %s, %s)"
        )
        conn.execute(text, (OPERATOR_ID_2, EXPERIMENT_ID, TASK_ID, PARAMETERS_JSON, DEPENDENCIES_OP_ID_JSON, CREATED_AT, UPDATED_AT,))

        text = (
            f"INSERT INTO operators (uuid, experiment_id, task_id, parameters, dependencies, created_at, updated_at) "
            f"VALUES (%s, %s, %s, %s, %s, %s, %s)"
        )
        conn.execute(text, (OPERATOR_ID_3, EXPERIMENT_ID_2, TASK_ID_3, PARAMETERS_JSON_2, DEPENDENCIES_OP_ID_JSON, CREATED_AT, UPDATED_AT,))

        text = (
            f"INSERT INTO operators (uuid, experiment_id, task_id, parameters, dependencies, created_at, updated_at) "
            f"VALUES (%s, %s, %s, %s, %s, %s, %s)"
        )
        conn.execute(text, (OPERATOR_ID_4, EXPERIMENT_ID_3, TASK_ID, PARAMETERS_JSON, DEPENDENCIES_OP_ID_JSON, CREATED_AT, UPDATED_AT,))

        text = (
            f"INSERT INTO operators (uuid, experiment_id, task_id, parameters, created_at, dependencies, updated_at) "
            f"VALUES (%s, %s, %s, %s, %s, %s, %s)"
        )
        conn.execute(text, (OPERATOR_ID_5, EXPERIMENT_ID_4, TASK_ID_4, PARAMETERS_JSON, DEPENDENCIES_OP_ID_JSON, CREATED_AT, UPDATED_AT,))

        text = (
            f"INSERT INTO templates (uuid, name, tasks, created_at, updated_at) "
            f"VALUES (%s, %s, %s, %s, %s)"
        )
        conn.execute(text, (TEMPLATE_ID, NAME, TASKS_JSON, CREATED_AT, UPDATED_AT,))
        conn.close()

    def tearDown(self):
        conn = engine.connect()

        text = f"DELETE FROM templates WHERE uuid = '{TEMPLATE_ID}'"
        conn.execute(text)

        text = f"DELETE FROM operators WHERE experiment_id = '{EXPERIMENT_ID}'"
        conn.execute(text)

        text = f"DELETE FROM operators WHERE experiment_id = '{EXPERIMENT_ID_2}'"
        conn.execute(text)

        text = f"DELETE FROM operators WHERE experiment_id = '{EXPERIMENT_ID_3}'"
        conn.execute(text)

        text = f"DELETE FROM operators WHERE experiment_id = '{EXPERIMENT_ID_4}'"
        conn.execute(text)

        text = (
            f"DELETE FROM operators WHERE experiment_id = "
            f"(SELECT uuid FROM experiments where name = '{NAME_COPYFROM}')"
        )
        conn.execute(text)

        text = f"DELETE FROM experiments WHERE project_id in ('{PROJECT_ID}')"
        conn.execute(text)

        text = f"DELETE FROM projects WHERE uuid = '{PROJECT_ID}'"
        conn.execute(text)

        text = f"DELETE FROM tasks WHERE uuid = '{TASK_ID_4}'"
        conn.execute(text)

        text = f"DELETE FROM tasks WHERE uuid = '{TASK_ID_3}'"
        conn.execute(text)

        text = f"DELETE FROM tasks WHERE uuid = '{TASK_ID_2}'"
        conn.execute(text)

        text = f"DELETE FROM tasks WHERE uuid = '{TASK_ID}'"
        conn.execute(text)

        conn.close()

    def test_list_experiments(self):
        rv = TEST_CLIENT.get("/projects/unk/experiments")
        result = rv.json()
        expected = {"message": "The specified project does not exist"}
        self.assertDictEqual(expected, result)
        self.assertEqual(rv.status_code, 404)

        rv = TEST_CLIENT.get(f"/projects/{PROJECT_ID}/experiments")
        result = rv.json()
        self.assertIsInstance(result["experiments"], list)
        self.assertIsInstance(result["total"], int)
        self.assertEqual(rv.status_code, 200)

    def test_create_experiment(self):
        rv = TEST_CLIENT.post("/projects/unk/experiments", json={})
        result = rv.json()
        expected = {"message": "The specified project does not exist"}
        self.assertDictEqual(expected, result)
        self.assertEqual(rv.status_code, 404)

        rv = TEST_CLIENT.post(f"/projects/{PROJECT_ID}/experiments", json={})
        result = rv.json()
        expected = {"message": "name is required"}
        self.assertDictEqual(expected, result)
        self.assertEqual(rv.status_code, 400)

        rv = TEST_CLIENT.post(f"/projects/{PROJECT_ID}/experiments", json={
            "name": NAME,
        })
        result = rv.json()
        expected = {"message": "an experiment with that name already exists"}
        self.assertDictEqual(expected, result)
        self.assertEqual(rv.status_code, 400)

        rv = TEST_CLIENT.post(f"/projects/{PROJECT_ID}/experiments", json={
            "name": "test",
        })
        result = rv.json()
        expected = {
            "name": "test",
            "projectId": PROJECT_ID,
            "position": 4,
            "isActive": IS_ACTIVE,
            "operators": [],
            "deployments": [],
        }
        # uuid, created_at, updated_at are machine-generated
        # we assert they exist, but we don't assert their values
        machine_generated = ["uuid", "createdAt", "updatedAt"]
        for attr in machine_generated:
            self.assertIn(attr, result)
            del result[attr]
        self.assertDictEqual(expected, result)

        """Copy operators for a given experiment"""
        rv = TEST_CLIENT.post(f"/projects/{PROJECT_ID}/experiments", json={
            "name": f"{NAME_COPYFROM}",
            "copyFrom": f"{EXPERIMENT_ID}"
        })
        self.assertEqual(rv.status_code, 200)

        rv = TEST_CLIENT.post(f"/projects/{PROJECT_ID}/experiments", json={
            "name": f"test copyFrom 2",
            "copyFrom": f"4555"
        })
        self.assertEqual(rv.status_code, 400)

    def test_get_experiment(self):
        rv = TEST_CLIENT.get(f"/projects/foo/experiments/{EXPERIMENT_ID}")
        result = rv.json()
        expected = {"message": "The specified project does not exist"}
        self.assertDictEqual(expected, result)
        self.assertEqual(rv.status_code, 404)

        rv = TEST_CLIENT.get(f"/projects/{PROJECT_ID}/experiments/foo")
        result = rv.json()
        expected = {"message": "The specified experiment does not exist"}
        self.assertDictEqual(expected, result)
        self.assertEqual(rv.status_code, 404)

        rv = TEST_CLIENT.get(f"/projects/{PROJECT_ID}/experiments/{EXPERIMENT_ID_2}")
        result = rv.json()
        expected = {
            "uuid": EXPERIMENT_ID_2,
            "name": NAME_2,
            "deployments": [],
            "projectId": PROJECT_ID,
            "position": POSITION_2,
            "isActive": IS_ACTIVE,
            "operators": result['operators'],
            "createdAt": CREATED_AT_ISO,
            "updatedAt": UPDATED_AT_ISO,
        }
        self.assertDictEqual(expected, result)
        operator = result["operators"][0]
        self.assertEqual("Unset", operator["status"])

        rv = TEST_CLIENT.get(f"/projects/{PROJECT_ID}/experiments/{EXPERIMENT_ID_3}")
        result = rv.json()
        expected = {
            "uuid": EXPERIMENT_ID_3,
            "name": NAME_3,
            "deployments": [],
            "projectId": PROJECT_ID,
            "position": POSITION_3,
            "isActive": IS_ACTIVE,
            "operators": result['operators'],
            "createdAt": CREATED_AT_ISO,
            "updatedAt": UPDATED_AT_ISO,
        }
        self.assertDictEqual(expected, result)
        operator = result["operators"][0]
        self.assertEqual("Unset", operator["status"])

        rv = TEST_CLIENT.get(f"/projects/{PROJECT_ID}/experiments/{EXPERIMENT_ID_4}")
        result = rv.json()
        expected = {
            "uuid": EXPERIMENT_ID_4,
            "name": NAME_4,
            "deployments": [],
            "projectId": PROJECT_ID,
            "position": POSITION_4,
            "isActive": IS_ACTIVE,
            "operators": result['operators'],
            "createdAt": CREATED_AT_ISO,
            "updatedAt": UPDATED_AT_ISO,
        }
        self.assertDictEqual(expected, result)
        operator = result["operators"][0]
        self.assertEqual("Setted up", operator["status"])

    def test_update_experiment(self):
        rv = TEST_CLIENT.patch(f"/projects/foo/experiments/{EXPERIMENT_ID}", json={})
        result = rv.json()
        expected = {"message": "The specified project does not exist"}
        self.assertDictEqual(expected, result)
        self.assertEqual(rv.status_code, 404)

        rv = TEST_CLIENT.patch(f"/projects/{PROJECT_ID}/experiments/foo", json={})
        result = rv.json()
        expected = {"message": "The specified experiment does not exist"}
        self.assertDictEqual(expected, result)
        self.assertEqual(rv.status_code, 404)

        rv = TEST_CLIENT.patch(f"/projects/{PROJECT_ID}/experiments/{EXPERIMENT_ID}", json={
            "name": NAME_2,
        })
        result = rv.json()
        expected = {"message": "an experiment with that name already exists"}
        self.assertDictEqual(expected, result)
        self.assertEqual(rv.status_code, 400)

        rv = TEST_CLIENT.patch(f"/projects/{PROJECT_ID}/experiments/{EXPERIMENT_ID}", json={
            "templateId": "unk",
        })
        result = rv.json()
        expected = {"message": "The specified template does not exist"}
        self.assertDictEqual(expected, result)
        self.assertEqual(rv.status_code, 400)

        rv = TEST_CLIENT.patch(f"/projects/{PROJECT_ID}/experiments/{EXPERIMENT_ID}", json={
            "unk": "bar",
        })
        self.assertEqual(rv.status_code, 400)

        # update experiment using the same name
        rv = TEST_CLIENT.patch(f"/projects/{PROJECT_ID}/experiments/{EXPERIMENT_ID}", json={
            "name": NAME,
        })
        self.assertEqual(rv.status_code, 200)

        rv = TEST_CLIENT.patch(f"/projects/{PROJECT_ID}/experiments/{EXPERIMENT_ID}", json={
            "name": "bar",
        })
        result = rv.json()
        expected = {
            "uuid": EXPERIMENT_ID,
            "name": "bar",
            "projectId": PROJECT_ID,
            "position": POSITION,
            "isActive": IS_ACTIVE,
            "operators": result['operators'],
            "createdAt": CREATED_AT_ISO,
            "deployments": [],
        }
        machine_generated = ["updatedAt"]
        for attr in machine_generated:
            self.assertIn(attr, result)
            del result[attr]
        self.assertDictEqual(expected, result)
        self.assertEqual(rv.status_code, 200)

        rv = TEST_CLIENT.patch(f"/projects/{PROJECT_ID}/experiments/{EXPERIMENT_ID}", json={
            "templateId": TEMPLATE_ID,
        })
        result = rv.json()
        expected = {
            "uuid": EXPERIMENT_ID,
            "name": "bar",
            "projectId": PROJECT_ID,
            "position": POSITION,
            "isActive": IS_ACTIVE,
            "createdAt": CREATED_AT_ISO,
            "deployments": [],
        }
        result_operators = result["operators"]
        machine_generated = ["updatedAt", "operators"]
        for attr in machine_generated:
            self.assertIn(attr, result)
            del result[attr]
        self.assertDictEqual(expected, result)
        expected = [{
            "taskId": TASK_ID_2,
            "experimentId": EXPERIMENT_ID,
            "parameters": {},
            "positionX": 200.0,
            "positionY": 0.0,
            "status": "Setted up",
            "deploymentId": None
        }, {
            "taskId": TASK_ID,
            "experimentId": EXPERIMENT_ID,
            "parameters": {},
            "positionX": 0.0,
            "positionY": 0.0,
            "status": "Setted up",
            "deploymentId": None
        }]
        machine_generated = ["uuid", "dependencies", "createdAt", "updatedAt"]
        for attr in machine_generated:
            for operator in result_operators:
                self.assertIn(attr, operator)
                del operator[attr]
        self.assertCountEqual(expected, result_operators)

    def test_delete_experiment(self):
        rv = TEST_CLIENT.delete(f"/projects/foo/experiments/{EXPERIMENT_ID}")
        result = rv.json()
        expected = {"message": "The specified project does not exist"}
        self.assertDictEqual(expected, result)
        self.assertEqual(rv.status_code, 404)

        rv = TEST_CLIENT.delete(f"/projects/{PROJECT_ID}/experiments/unk")
        result = rv.json()
        expected = {"message": "The specified experiment does not exist"}
        self.assertDictEqual(expected, result)
        self.assertEqual(rv.status_code, 404)

        rv = TEST_CLIENT.delete(f"/projects/{PROJECT_ID}/experiments/{EXPERIMENT_ID}")
        result = rv.json()
        expected = {"message": "Experiment deleted"}
        self.assertDictEqual(expected, result)
