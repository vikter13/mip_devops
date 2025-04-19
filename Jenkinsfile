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
        stage('Run Tests') {
            parallel {
                stage('Code Quality') {
                    steps {
                        sh '''
                            . venv/bin/activate
                            
                            cd /root/oboldui/mip_devops
                            
                            echo "Scanning Python files in: $(pwd)"
                            find . -name "*.py" | xargs pylint --exit-zero > pylint_report.txt
                            
                            echo "=== Pylint Report ==="
                            cat pylint_report.txt
                            
                            ERROR_COUNT=$(grep -E '^[EF]' pylint_report.txt | wc -l)
                            if [ "$ERROR_COUNT" -gt 0 ]; then
                                echo "Found $ERROR_COUNT Pylint errors (level E/F):"
                                grep -E '^[EF]' pylint_report.txt
                                exit 1  
                            else
                                echo "No Pylint errors (level E/F) found."
                            fi
                        '''
                    }
                }

                stage('Security Scan') {
                    steps {
                        sh '''
                            . venv/bin/activate
                            
                            cd /root/oboldui/mip_devops
                            
                            echo "Running Bandit scan in: $(pwd)"
                            bandit -r . --exclude ./venv -f json -o bandit_report.json || true
                            
                            echo "=== Bandit Report Summary ==="
                            cat bandit_report.json
                            
                            if jq -e '.results[] | select(.issue_severity == "CRITICAL")' bandit_report.json >/dev/null; then
                                echo "ERROR: Bandit detected CRITICAL vulnerabilities:"
                                jq '.results[] | select(.issue_severity == "CRITICAL")' bandit_report.json
                                exit 1
                            else
                                echo "No CRITICAL vulnerabilities found."
                            fi
                        '''
                    }
                }

                stage('Secrets Detection') {
                    steps {
                        sh '''
                            . venv/bin/activate
                            
                            cd /root/oboldui/mip_devops
                            
                            echo "Scanning for secrets in: $(pwd)"
                            trufflehog filesystem . --json > trufflehog_report.json || true
                            
                            echo "=== TruffleHog Report ==="
                            cat trufflehog_report.json
                            
                            if [ -s trufflehog_report.json ]; then
                                echo "ERROR: TruffleHog detected secrets in /root/oboldui/mip_devops!"
                                exit 1
                            else
                                echo "No secrets found."
                            fi
                        '''
                    }
                }
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
