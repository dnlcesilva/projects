# -*- coding: utf-8 -*-
from io import BytesIO
from json import dumps
from unittest import TestCase

from fastapi.testclient import TestClient

from minio.error import BucketAlreadyOwnedByYou

from projects.api.main import app
from projects.controllers.utils import uuid_alpha
from projects.database import engine
from projects.object_storage import BUCKET_NAME, MINIO_CLIENT

TEST_CLIENT = TestClient(app)

TASK_ID = str(uuid_alpha())
NAME = "foo"
DESCRIPTION = "long foo"
IMAGE = "platiagro/platiagro-experiment-image:0.2.0"
COMMANDS = ["CMD"]
COMMANDS_JSON = dumps(COMMANDS)
ARGUMENTS = ["ARG"]
ARGUMENTS_JSON = dumps(ARGUMENTS)
TAGS = ["PREDICTOR"]
TAGS_JSON = dumps(TAGS)
EXPERIMENT_NOTEBOOK_PATH = f"minio://{BUCKET_NAME}/tasks/{TASK_ID}/Experiment.ipynb"
DEPLOYMENT_NOTEBOOK_PATH = f"minio://{BUCKET_NAME}/tasks/{TASK_ID}/Deployment.ipynb"
CREATED_AT = "2000-01-01 00:00:00"
UPDATED_AT = "2000-01-01 00:00:00"


class TestParameters(TestCase):

    def setUp(self):
        self.maxDiff = None
        conn = engine.connect()
        text = (
            f"INSERT INTO tasks (uuid, name, description, image, commands, arguments, tags, parameters, experiment_notebook_path, deployment_notebook_path, is_default, created_at, updated_at) "
            f"VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )
        conn.execute(text, (TASK_ID, NAME, DESCRIPTION, IMAGE, COMMANDS_JSON, ARGUMENTS_JSON, TAGS_JSON,
                            dumps([]), EXPERIMENT_NOTEBOOK_PATH, DEPLOYMENT_NOTEBOOK_PATH, 0, CREATED_AT, UPDATED_AT,))
        conn.close()

        try:
            MINIO_CLIENT.make_bucket(BUCKET_NAME)
        except BucketAlreadyOwnedByYou:
            pass

        file = BytesIO(b'{"cells":[{"cell_type":"code","execution_count":null,"metadata":{},"outputs":[],"source":[]}],"metadata":{"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},"language_info":{"codemirror_mode":{"name":"ipython","version":3},"file_extension":".py","mimetype":"text/x-python","name":"python","nbconvert_exporter":"python","pygments_lexer":"ipython3","version":"3.6.9"}},"nbformat":4,"nbformat_minor":4}')
        MINIO_CLIENT.put_object(
            bucket_name=BUCKET_NAME,
            object_name=EXPERIMENT_NOTEBOOK_PATH[len(f"minio://{BUCKET_NAME}/"):],
            data=file,
            length=file.getbuffer().nbytes,
        )

    def tearDown(self):
        conn = engine.connect()
        text = f"DELETE FROM tasks WHERE uuid = '{TASK_ID}'"
        conn.execute(text)
        conn.close()

        prefix = f"tasks/{TASK_ID}"
        for obj in MINIO_CLIENT.list_objects(BUCKET_NAME, prefix=prefix, recursive=True):
            MINIO_CLIENT.remove_object(BUCKET_NAME, obj.object_name)

    def test_list_parameters(self):
        rv = TEST_CLIENT.get("/tasks/unk/parameters")
        result = rv.json()
        expected = {"message": "The specified task does not exist"}
        self.assertDictEqual(expected, result)
        self.assertEqual(rv.status_code, 404)

        rv = TEST_CLIENT.get(f"/tasks/{TASK_ID}/parameters")
        result = rv.json()
        self.assertIsInstance(result, list)
