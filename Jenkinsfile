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

        stage('Install Analyzers') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install -r requirements.txt
                    pip install pylint bandit trufflehog
                '''
            }
        }
        stage('Code Quality') {
            steps {
                // Запускаем Pylint и останавливаем билд при ошибках уровней E или F
                sh '''
                    . venv/bin/activate
                    pylint app.py database.py forms.py --exit-zero > pylint_report.txt
                    echo "Pylint Report:"
                    cat pylint_report.txt
                    echo "Ошибки уровней E и F:"
                    grep -E '^[EF]' pylint_report.txt || echo "Нет ошибок уровней E или F"
                '''
            }
        }
        stage('Security Scan') {
            steps {
                // Запускаем Bandit, сохраняем отчёт и падаем при CRITICAL
                sh '''
                    . venv/bin/activate
                    bandit -r . -f json -o bandit_report.json || true

                    echo "=== Bandit JSON Report ==="
                    cat bandit_report.json

                    if grep -q '"issue_severity": "CRITICAL"' bandit_report.json; then
                        echo "Bandit detected CRITICAL vulnerabilities"
                        exit 1
                    fi
                '''
            }
        }
        stage('Secrets Detection') {
            steps {
                // Запускаем TruffleHog и падаем при любом найденном секрете
                sh '''
                    . venv/bin/activate
                    trufflehog filesystem . --json > trufflehog_report.json || true
                    if [ -s trufflehog_report.json ]; then
                        echo "TruffleHog detected secrets"
                        exit 1
                    fi
                '''
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
                    #!/bin/bash
                    echo "$REGISTRY_CREDS_PSW" | docker login -u "$REGISTRY_CREDS_USR" --password-stdin "$REGISTRY_ADDRESS"
                    docker push "$DOCKER_IMAGE:$BUILD_NUMBER"
                    docker push "$DOCKER_IMAGE:latest"
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
