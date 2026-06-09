pipeline {
    agent any

    environment {
        DOCKER_IMAGE = "hbhangale3/astra-rag"
        DOCKERHUB_CREDENTIALS = "dockerhub-token"
        GITHUB_CREDENTIALS = "github-token"
        GIT_REPO_URL = "github.com/hbhangale3/Astra-RAG-Chatbot.git"
    }

    stages {
        stage("Checkout") {
            steps {
                echo "Checking out source code..."
                checkout scm
            }
        }

        stage("Skip CI Check") {
            steps {
                script {
                    def lastCommitMessage = sh(
                        script: "git log -1 --pretty=%B",
                        returnStdout: true
                    ).trim()

                    echo "Last commit message: ${lastCommitMessage}"

                    if (lastCommitMessage.contains("[skip ci]")) {
                        echo "Commit contains [skip ci]. Skipping pipeline."
                        currentBuild.result = "SUCCESS"
                        return
                    }
                }
            }
        }

        stage("Detect Changes") {
            steps {
                sh '''
                    set -e

                    echo "Detecting changed files..."

                    if git rev-parse HEAD~1 >/dev/null 2>&1; then
                        git diff --name-only HEAD~1 HEAD > changed_files.txt
                    else
                        git ls-files > changed_files.txt
                    fi

                    echo "Changed files:"
                    cat changed_files.txt

                    echo "false" > .should_build_image

                    if grep -qE "^(Dockerfile|run_astra.sh|pyproject.toml|uv.lock)$|^src/|^\\.streamlit/" changed_files.txt; then
                        echo "true" > .should_build_image
                        git rev-parse --short=8 HEAD > .image_tag
                        echo "Docker-relevant change detected."
                        echo "Image tag will be: $(cat .image_tag)"
                    else
                        echo "No Docker-relevant changes detected. Skipping Docker build."
                    fi
                '''
            }
        }

        stage("Verify Docker") {
            when {
                expression { fileExists(".should_build_image") && readFile(".should_build_image").trim() == "true" }
            }
            steps {
                echo "Verifying Docker inside Jenkins..."
                sh "docker --version"
                sh "docker ps"
            }
        }

        stage("Build Docker Image") {
            when {
                expression { fileExists(".should_build_image") && readFile(".should_build_image").trim() == "true" }
            }
            steps {
                sh '''
                    set -e
                    IMAGE_TAG=$(cat .image_tag)

                    echo "Building Docker image ${DOCKER_IMAGE}:${IMAGE_TAG}..."
                    docker build -t ${DOCKER_IMAGE}:${IMAGE_TAG} .
                    docker tag ${DOCKER_IMAGE}:${IMAGE_TAG} ${DOCKER_IMAGE}:latest
                '''
            }
        }

        stage("Login to DockerHub") {
            when {
                expression { fileExists(".should_build_image") && readFile(".should_build_image").trim() == "true" }
            }
            steps {
                echo "Logging in to DockerHub..."
                withCredentials([usernamePassword(
                    credentialsId: "${DOCKERHUB_CREDENTIALS}",
                    usernameVariable: "DOCKERHUB_USERNAME",
                    passwordVariable: "DOCKERHUB_TOKEN"
                )]) {
                    sh '''
                        echo "$DOCKERHUB_TOKEN" | docker login -u "$DOCKERHUB_USERNAME" --password-stdin
                    '''
                }
            }
        }

        stage("Push Docker Image") {
            when {
                expression { fileExists(".should_build_image") && readFile(".should_build_image").trim() == "true" }
            }
            steps {
                sh '''
                    set -e
                    IMAGE_TAG=$(cat .image_tag)

                    echo "Pushing Docker image ${DOCKER_IMAGE}:${IMAGE_TAG}..."
                    docker push ${DOCKER_IMAGE}:${IMAGE_TAG}

                    echo "Pushing Docker image ${DOCKER_IMAGE}:latest..."
                    docker push ${DOCKER_IMAGE}:latest
                '''
            }
        }

        stage("Update Kubernetes Manifests") {
            when {
                expression { fileExists(".should_build_image") && readFile(".should_build_image").trim() == "true" }
            }
            steps {
                sh '''
                    set -e
                    IMAGE_TAG=$(cat .image_tag)

                    echo "Updating Kubernetes manifests with image tag ${IMAGE_TAG}..."

                    sed -i "s|image: hbhangale3/astra-rag:.*|image: hbhangale3/astra-rag:${IMAGE_TAG}|g" k8s/backend-deployment.yaml
                    sed -i "s|image: hbhangale3/astra-rag:.*|image: hbhangale3/astra-rag:${IMAGE_TAG}|g" k8s/frontend-deployment.yaml

                    echo "Updated image references:"
                    grep -R "image: hbhangale3/astra-rag" -n k8s
                '''
            }
        }

        stage("Commit Manifest Update") {
            when {
                expression { fileExists(".should_build_image") && readFile(".should_build_image").trim() == "true" }
            }
            steps {
                echo "Committing updated manifests back to GitHub..."
                withCredentials([usernamePassword(
                    credentialsId: "${GITHUB_CREDENTIALS}",
                    usernameVariable: "GITHUB_USERNAME",
                    passwordVariable: "GITHUB_TOKEN"
                )]) {
                    sh '''
                        set -e
                        IMAGE_TAG=$(cat .image_tag)

                        git config user.email "jenkins@astra-rag.local"
                        git config user.name "Jenkins CI"

                        git add k8s/backend-deployment.yaml k8s/frontend-deployment.yaml

                        if git diff --cached --quiet; then
                            echo "No manifest changes to commit."
                        else
                            git commit -m "ci: update image tag to ${IMAGE_TAG} [skip ci]"
                            git push https://${GITHUB_USERNAME}:${GITHUB_TOKEN}@${GIT_REPO_URL} HEAD:main
                        fi
                    '''
                }
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