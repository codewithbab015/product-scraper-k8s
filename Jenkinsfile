pipeline {
    agent any

    environment {
        // Auth and Git source
        GIT_URL = 'https://github.com/codewithbab015/amazon-scraper-dockerized.git'
        GIT_CREDENTIALS_ID = 'github_token_id'
        DOCKERHUB_CREDENTIALS_ID = 'docker_token_id'

        // Python env
        PIP_CACHE_DIR = "${WORKSPACE}/.pip_cache"
        VENV_DIR = "${WORKSPACE}/.venv"

        // Taskfile args
        RUN_GROUP = "electronics"
        RUN_NAME = "camera-photo"
        MAX_PAGE = "1"
        DESTINATION = "dir"
        LIMIT_RECORDS = "1"

        // Docker image metadata
        DOCKER_USER = "mrbaloyin"
        DOCKER_IMG = "amazon-web-scraper-cli"
    }

    stages {
        stage('Clone Source-Code') {
            steps {
                echo '📥 Cloning source code from Git...'
                checkout scmGit(
                    branches: [[name: '*/main']],
                    userRemoteConfigs: [[
                        credentialsId: "${env.GIT_CREDENTIALS_ID}",
                        url: "${env.GIT_URL}"
                    ]]
                )
                echo '✅ Repository successfully cloned.'
            }
        }

        stage('Python Env-Setup') {
            steps {
                sh '''#!/bin/bash
                    echo "🔧 Setting up Python virtual environment..."
                    set -e
                    chmod +x activate_venv_ci.sh
                    ./activate_venv_ci.sh
                    echo "✅ Python environment setup complete."
                '''
            }
        }

        stage('Build') {
            steps {
                script {
                    def gitSha = sh(script: "git rev-parse --short HEAD", returnStdout: true).trim()
                    env.DOCKER_TAG = "${env.DOCKER_USER}/${env.DOCKER_IMG}:${gitSha}"

                    withCredentials([usernamePassword(
                        credentialsId: env.DOCKERHUB_CREDENTIALS_ID,
                        usernameVariable: 'DOCKER_USER',
                        passwordVariable: 'DOCKER_PASS'
                    )]) {
                        sh '''#!/bin/bash
                            echo "🔐 Logging into Docker Hub..."
                            echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                        '''
                    }

                    sh '''#!/bin/bash
                        set -e
                        source "$VENV_DIR/bin/activate"
                        echo "🐳 Building Docker image using Taskfile..."
                        task docker:local-build DOCKER_TAG=$DOCKER_TAG
                        docker images
                    '''
                }
            }
        }

        stage('Test') {
            steps {
                sh '''#!/bin/bash
                    set -e
                    source "$VENV_DIR/bin/activate"
                    task default
                    echo "🧪 Starting ETL test runs..."
                    task docker:run-jobs \
                        DOCKER_TAG=$DOCKER_TAG \
                        MAX=$MAX_PAGE \
                        DESTINATION=$DESTINATION \
                        RUN_GROUP=$RUN_GROUP \
                        RUN_NAME=$RUN_NAME > task_run.log 2>&1
                    echo "✅ ETL test runs complete."
                '''
            }
        }

        stage('Deploy') {
            steps {
                sh '''#!/bin/bash
                    set -e
                    echo "📤 Pushing Docker image to Docker Hub..."
                    docker push $DOCKER_TAG

                    echo "🆕 Tagging as 'latest'..."
                    docker tag $DOCKER_TAG $DOCKER_USER/$DOCKER_IMG:latest
                    docker push $DOCKER_USER/$DOCKER_IMG:latest
                '''
            }
        }
    }

    post {
        always {
            echo '📦 Archiving logs and pip cache...'
            archiveArtifacts artifacts: '.pip_cache/**', fingerprint: true
            archiveArtifacts artifacts: 'task_run.log', fingerprint: true
        }
    }
}
