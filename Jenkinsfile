pipeline {
    agent any

    environment {
        NEXUS_URL = 'localhost:8082'
        IMAGE_TAG = "v${BUILD_NUMBER}"
        NAMESPACE = 'devops-pipeline'
    }

    stages {

        stage('Clone') {
            steps {
                echo 'Code récupéré depuis GitHub'
            }
        }

        stage('Build Images') {
            steps {
                sh 'docker build -t app-users:${IMAGE_TAG} ./app-users'
                sh 'docker build -t app-products:${IMAGE_TAG} ./app-products'
            }
        }

        stage('Push to Nexus') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'nexus-credentials',
                    usernameVariable: 'NEXUS_USER',
                    passwordVariable: 'NEXUS_PASS'
                )]) {
                    sh 'echo $NEXUS_PASS | docker login ${NEXUS_URL} -u $NEXUS_USER --password-stdin'
                    sh 'docker tag app-users:${IMAGE_TAG} ${NEXUS_URL}/app-users:${IMAGE_TAG}'
                    sh 'docker tag app-products:${IMAGE_TAG} ${NEXUS_URL}/app-products:${IMAGE_TAG}'
                    sh 'docker push ${NEXUS_URL}/app-users:${IMAGE_TAG}'
                    sh 'docker push ${NEXUS_URL}/app-products:${IMAGE_TAG}'
                }
            }
        }

        stage('Deploy to Minikube') {
            steps {
                sh 'minikube image load app-users:${IMAGE_TAG}'
                sh 'minikube image load app-products:${IMAGE_TAG}'
                sh 'kubectl set image deployment/app-users app-users=app-users:${IMAGE_TAG} -n ${NAMESPACE}'
                sh 'kubectl set image deployment/app-products app-products=app-products:${IMAGE_TAG} -n ${NAMESPACE}'
            }
        }
    }

    post {
        success {
            echo 'Pipeline terminé avec succès'
        }
        failure {
            echo 'Pipeline échoué'
        }
    }
}
