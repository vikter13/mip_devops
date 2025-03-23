pipeline {
    agent any

    environment {
        DOCKER_HUB_CREDS = credentials('docker-hub-credentials')
        DOCKER_IMAGE = "romkapremium/flask_app"
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
        }

        stage('Push to Docker Hub') {
            steps {
                sh 'echo $DOCKER_HUB_CREDS_PSW | docker login -u $DOCKER_HUB_CREDS_USR --password-stdin'
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