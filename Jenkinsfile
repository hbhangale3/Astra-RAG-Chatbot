pipeline {
    agent any

    environment {
        DOCKER_IMAGE = "hbhangale3/astra-rag"
        DOCKER_TAG = "latest"
        DOCKERHUB_CREDENTIALS = "dockerhub-token"
    }

    stages {
        stage("Checkout") {
            steps {
                echo "Checking out source code..."
                checkout scm
            }
        }

        stage("Verify Docker") {
            steps {
                echo "Verifying Docker inside Jenkins..."
                sh "docker --version"
                sh "docker ps"
            }
        }

        stage("Build Docker Image") {
            steps {
                echo "Building Docker image..."
                sh "docker build -t ${DOCKER_IMAGE}:${DOCKER_TAG} ."
            }
        }

        stage("Login to DockerHub") {
            steps {
                echo "Logging in to DockerHub..."
                withCredentials([usernamePassword(
                    credentialsId: "${DOCKERHUB_CREDENTIALS}",
                    usernameVariable: "DOCKERHUB_USERNAME",
                    passwordVariable: "DOCKERHUB_TOKEN"
                )]) {
                    sh "echo $DOCKERHUB_TOKEN | docker login -u $DOCKERHUB_USERNAME --password-stdin"
                }
            }
        }

        stage("Push Docker Image") {
            steps {
                echo "Pushing Docker image to DockerHub..."
                sh "docker push ${DOCKER_IMAGE}:${DOCKER_TAG}"
            }
        }
    }

    post {
        success {
            echo "CI pipeline completed successfully."
        }
        failure {
            echo "CI pipeline failed."
        }
    }
}