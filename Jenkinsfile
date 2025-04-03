pipeline {
    agent any

    environment {
        REGISTRY_CREDS = credentials('local-registry-creds')
        REGISTRY_ADDRESS = "192.168.1.113:5000"
        DOCKER_IMAGE = "${REGISTRY_ADDRESS}/romka_premium/flask_app"
        GIT_CREDS = credentials('github-ssh-key')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: '*/main']],
                    userRemoteConfigs: [[
                        url: 'https://github.com/vikter13/mip_devops.git',
                        credentialsId: 'github-ssh-key'
                    ]]
                ])
            }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t $DOCKER_IMAGE:$BUILD_NUMBER .'
                sh 'docker tag $DOCKER_IMAGE:$BUILD_NUMBER $DOCKER_IMAGE:latest'
            }
        }

        stage('Push to Local Registry') {
            steps {
                sh '''
                    docker login -u $REGISTRY_CREDS_USR --password-stdin $REGISTRY_ADDRESS <<< $REGISTRY_CREDS_PSW
                    docker push $DOCKER_IMAGE:$BUILD_NUMBER
                    docker push $DOCKER_IMAGE:latest
                '''
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
            sh 'docker logout $REGISTRY_ADDRESS'
        }
    }
}
