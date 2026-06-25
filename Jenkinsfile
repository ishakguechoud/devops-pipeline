pipeline {
    agent any

    triggers {
        pollSCM('H/2 * * * *')
    }

    environment {
        NEXUS_URL = '192.168.74.128:8082'
        IMAGE_TAG = "v${BUILD_NUMBER}"
    }

    stages {
        stage('Clone') {
            steps {
                echo "Branch détectée : ${env.GIT_BRANCH}"
                checkout scm
            }
        }

        stage('Build Images') {
            steps {
                sh "docker build -t ${NEXUS_URL}/app-users:${IMAGE_TAG} ./app-users"
                sh "docker build -t ${NEXUS_URL}/app-products:${IMAGE_TAG} ./app-products"
                sh "docker build -t ${NEXUS_URL}/app-frontend:${IMAGE_TAG} ./app-frontend"
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

                    docker push ${NEXUS_URL}/app-users:${IMAGE_TAG}
                    docker push ${NEXUS_URL}/app-products:${IMAGE_TAG}
                    docker push ${NEXUS_URL}/app-frontend:${IMAGE_TAG}
                    """
                }
            }
        }

        stage('Deploy via Helm') {
            steps {
                script {
                    // Détermination de l'environnement selon la branche
                    def envName = "preprod"
                    def k8sNamespace = "preprod-platform"

                    if (env.GIT_BRANCH == 'origin/main' || env.GIT_BRANCH == 'main') {
                        envName = "prod"
                        k8sNamespace = "prod-platform"
                    }

                    echo "🌿 Branche : ${env.GIT_BRANCH}"
                    echo "🚀 Environnement : ${envName}"
                    echo "📦 Namespace : ${k8sNamespace}"

                    sh """
                    helm upgrade --install app-products ./app-products/chart \
                      --namespace ${k8sNamespace} --create-namespace \
                      --kubeconfig=/root/.kube/config \
                      -f ./app-products/chart/values-${envName}.yaml \
                      --set image.tag=${IMAGE_TAG}

                    helm upgrade --install app-users ./app-users/chart \
                      --namespace ${k8sNamespace} --create-namespace \
                      --kubeconfig=/root/.kube/config \
                      -f ./app-users/chart/values-${envName}.yaml \
                      --set image.tag=${IMAGE_TAG}

                    helm upgrade --install app-frontend ./app-frontend/chart \
                      --namespace ${k8sNamespace} --create-namespace \
                      --kubeconfig=/root/.kube/config \
                      -f ./app-frontend/chart/values-${envName}.yaml \
                      --set image.tag=${IMAGE_TAG}
                    """
                }
            }
        }
    }

    post {
        success {
            script {
                def envName = (env.GIT_BRANCH == 'origin/main' || env.GIT_BRANCH == 'main') ? 'PROD' : 'PREPROD'
                echo "✅ Pipeline terminé avec succès — déployé en ${envName}"
            }
        }
        failure {
            echo '❌ Pipeline échoué — vérifier les logs ci-dessus'
        }
    }
}