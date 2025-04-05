pipeline {
    agent any

    environment {
        DOCKER_HUB_CREDS = credentials('local-docker-hub')
        DOCKER_REGISTRY = "5.101.69.113:5000"
        DOCKER_IMAGE = "${DOCKER_REGISTRY}/nikitorik/flask_app"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t $DOCKER_IMAGE:$BUILD_NUMBER .'
                sh 'docker tag $DOCKER_IMAGE:$BUILD_NUMBER $DOCKER_IMAGE:latest'

        }

        stage('Push to Docker Hub') {
            steps {
                sh 'echo $DOCKER_REGISTRY_CREDS_PSW | docker login -u $DOCKER_REGISTRY_CREDS_USR $DOCKER_REGISTRY'
                sh 'docker push $DOCKER_IMAGE:$BUILD_NUMBER'
                sh 'docker push $DOCKER_IMAGE:latest'
            }
        }

        stage('Clean Up') {
            steps {
                sh 'docker rmi $DOCKER_IMAGE:$BUILD_NUMBER'
                sh 'docker rmi $DOCKER_IMAGE:latest'
            }
        }
    }

    post {
        always {
            sh 'docker logout'
        }
    }
}