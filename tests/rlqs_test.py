# Copyright 2024 gRPC authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import logging
from typing import TypeAlias

from absl import flags
from absl.testing import absltest

from framework import xds_k8s_testcase
from framework.test_app.runners.k8s import k8s_xds_server_runner

logger = logging.getLogger(__name__)
flags.adopt_module_key_flags(xds_k8s_testcase)

XdsTestServer: TypeAlias = xds_k8s_testcase.XdsTestServer
XdsTestClient: TypeAlias = xds_k8s_testcase.XdsTestClient
KubernetesServerRunner: TypeAlias = k8s_xds_server_runner.KubernetesServerRunner
ServerDeploymentArgs: TypeAlias = k8s_xds_server_runner.ServerDeploymentArgs


class RlqsTest(xds_k8s_testcase.AppNetXdsKubernetesTestCase):
    def initKubernetesServerRunner(self, **kwargs) -> KubernetesServerRunner:
        return super().initKubernetesServerRunner(
            deployment_args=ServerDeploymentArgs(enable_rlqs=True), **kwargs
        )

    def test_rate_limit(self) -> None:
        with self.subTest("0_create_health_check"):
            self.td.create_health_check()

        with self.subTest("1_create_backend_service"):
            self.td.create_backend_service()

        with self.subTest("2_create_mesh"):
            self.td.create_mesh()

        with self.subTest("3_create_grpc_route"):
            self.td.create_grpc_route(
                self.server_xds_host,
                self.server_xds_port,
            )

        with self.subTest("4_create_endpoint_policy"):
            self.td.create_endpoint_policy(
                server_namespace=self.server_namespace,
                server_name=self.server_name,
                server_port=self.server_port,
            )

        # TODO(sergiitk): create rl resources

        with self.subTest("4_start_test_server"):
            test_server: XdsTestServer = self.startTestServers()[0]

        with self.subTest("5_setup_server_backends"):
            self.setupServerBackends()

        with self.subTest("6_start_test_client"):
            test_client: XdsTestClient = self.startTestClient(
                test_server, config_mesh=self.td.mesh.name
            )

        with self.subTest("7_assert_xds_config_exists"):
            self.assertXdsConfigExists(test_client)

        # TODO(sergiitk): verify rl

        with self.subTest("8_assert_successful_rpcs"):
            self.assertSuccessfulRpcs(test_client)


if __name__ == "__main__":
    absltest.main()