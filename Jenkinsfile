pipeline {
    agent any

    environment {
        NEXUS_URL = '192.168.74.128:8082'
        IMAGE_TAG = "v${BUILD_NUMBER}"
        NAMESPACE = 'devops-pipeline'
    }

    stages {

        stage('Clone') {
            steps {
                echo 'Code recupere depuis GitHub'
            }
        }

        stage('Build Images') {
            steps {
                sh "docker build -t app-users:${IMAGE_TAG} ./app-users"
                sh "docker build -t app-products:${IMAGE_TAG} ./app-products"
                sh "docker build -t app-frontend:${IMAGE_TAG} ./app-frontend"
            }
        }

        stage('Push to Nexus') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'nexus-credentials',
                        usernameVariable: 'NEXUS_USER',
                        passwordVariable: 'NEXUS_PASS'
                    )
                ]) {
                    sh """
                    echo \$NEXUS_PASS | docker login ${NEXUS_URL} -u \$NEXUS_USER --password-stdin

                    docker tag app-users:${IMAGE_TAG} ${NEXUS_URL}/app-users:${IMAGE_TAG}
                    docker tag app-products:${IMAGE_TAG} ${NEXUS_URL}/app-products:${IMAGE_TAG}
                    docker tag app-frontend:${IMAGE_TAG} ${NEXUS_URL}/app-frontend:${IMAGE_TAG}

                    docker push ${NEXUS_URL}/app-users:${IMAGE_TAG}
                    docker push ${NEXUS_URL}/app-products:${IMAGE_TAG}
                    docker push ${NEXUS_URL}/app-frontend:${IMAGE_TAG}
                    
                    """
                }
            }
        }

        stage('Update Manifests') {
            steps {
                sh """
                sed -i "s|image: .*app-users:.*|image: ${NEXUS_URL}/app-users:${IMAGE_TAG}|g" k8s/app-users.yml
                sed -i "s|image: .*app-products:.*|image: ${NEXUS_URL}/app-products:${IMAGE_TAG}|g" k8s/app-products.yml
                sed -i "s|image: .*app-frontend:.*|image: ${NEXUS_URL}/app-frontend:${IMAGE_TAG}|g" k8s/app-frontend.yml
                """
            }
        }

        stage('Deploy to k3s') {
            steps {
                sh """
                kubectl apply -f k8s/app-users.yml -n ${NAMESPACE} --kubeconfig=/root/.kube/config
                kubectl apply -f k8s/app-products.yml -n ${NAMESPACE} --kubeconfig=/root/.kube/config
                kubectl apply -f k8s/app-frontend.yml -n ${NAMESPACE} --kubeconfig=/root/.kube/config
                """
            }
        }
    }

    post {
        success {
            echo 'Pipeline termine avec succes - deploye sur k3s'
        }

        failure {
            echo 'Pipeline echoue'
        }
    }
}
