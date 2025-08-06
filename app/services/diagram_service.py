import os
import uuid
import base64
import time
from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import EC2, Lambda
from diagrams.aws.database import RDS, Dynamodb
from diagrams.aws.network import ELB, APIGateway, VPC, InternetGateway
from diagrams.aws.storage import S3
from diagrams.aws.integration import SQS, SNS
from diagrams.aws.management import Cloudwatch
from diagrams.aws.security import IAM, Cognito
from diagrams.aws.analytics import Kinesis
from diagrams.aws.devtools import Codebuild, Codepipeline
from app.agents.diagram_agent import DiagramAgent

class DiagramService:
    def __init__(self, temp_dir="/tmp/diagrams"):
        self.temp_dir = temp_dir
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
        self.agent = DiagramAgent()

    async def generate_diagram_from_description(self, description: str):
        analysis_result = await self.agent.generate_analysis(description)

        node_map = {
            # Compute
            "ec2": EC2,
            "lambda": Lambda,

            # Database
            "rds": RDS,
            "dynamodb": Dynamodb,

            # Network & Load Balancing
            "elb": ELB,
            "alb": ELB,  # Application Load Balancer
            "nlb": ELB,  # Network Load Balancer
            "api_gateway": APIGateway,
            "apigateway": APIGateway,
            "vpc": VPC,
            "internet_gateway": InternetGateway,

            # Storage
            "s3": S3,

            # Integration & Messaging
            "sqs": SQS,
            "sns": SNS,

            # Management & Monitoring
            "cloudwatch": Cloudwatch,
            "monitoring": Cloudwatch,

            # Security
            "iam": IAM,
            "cognito": Cognito,

            # Analytics
            "kinesis": Kinesis,

            # Developer Tools
            "codebuild": Codebuild,
            "codepipeline": Codepipeline,

            # Generic service types
            "service": Lambda,  # Default for microservices
            "microservice": Lambda,
            "auth_service": Cognito,
            "payment_service": Lambda,
            "order_service": Lambda,
            "web_server": EC2,
            "database": RDS,
            "queue": SQS,
            "gateway": APIGateway,
        }

        diagram_path = os.path.join(self.temp_dir, str(uuid.uuid4()))
        nodes = {}
        start_time = time.time()

        with Diagram(description, filename=diagram_path, show=False, outformat="png") as diag:
            # Create clusters and the nodes within them
            for cluster_info in analysis_result.get("clusters", []):
                with Cluster(cluster_info["label"]) as cluster:
                    for node_id in cluster_info["nodes"]:
                        node_details = next((n for n in analysis_result["nodes"] if n["id"] == node_id), None)
                        if node_details:
                            node_class = node_map.get(node_details["type"].lower())
                            if node_class:
                                nodes[node_id] = node_class(node_details["label"])

            # Create standalone nodes
            clustered_node_ids = [node_id for c in analysis_result.get("clusters", []) for node_id in c["nodes"]]
            for node_details in analysis_result["nodes"]:
                if node_details["id"] not in clustered_node_ids:
                    node_class = node_map.get(node_details["type"].lower())
                    if node_class:
                        nodes[node_details["id"]] = node_class(node_details["label"])

            # Create connections
            for conn in analysis_result.get("connections", []):
                source_node = nodes.get(conn["source"])
                target_node = nodes.get(conn["target"])
                if source_node and target_node:
                    source_node >> target_node

        generation_time = time.time() - start_time
        image_path = f"{diagram_path}.png"

        if not os.path.exists(image_path):
            raise FileNotFoundError("Diagram image not generated.")

        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        os.remove(image_path)

        metadata = {
            "nodes_created": len(analysis_result.get("nodes", [])),
            "clusters_created": len(analysis_result.get("clusters", [])),
            "connections_made": len(analysis_result.get("connections", [])),
            "generation_time": generation_time
        }

        return image_data, metadata