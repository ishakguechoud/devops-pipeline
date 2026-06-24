pipeline {
    agent any

    environment {
        NEXUS_URL = '192.168.74.128:8082'
        IMAGE_TAG = "v${BUILD_NUMBER}"
        // On supprime la variable NAMESPACE fixe car elle va devenir dynamique !
    }

    stages {
        stage('Clone') {
            steps {
                echo 'Code recupere depuis GitHub'
                checkout scm // Ligne standard pour s'assurer que Jenkins récupère bien le code
            }
        }

        stage('Build Images') {
            steps {
                // On build directement avec l'URL Nexus pour s'éviter l'étape de "docker tag" après
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

        // L'ancien stage "Update Manifests" avec les `sed` disparaît complètement !
        // Helm gère la mise à jour des tags dynamiquement.

        stage('Deploy via Helm') {
            steps {
                script {
                    // --- DÉTERMINATION DE L'ENVIRONNEMENT ---
                    def envName = "preprod"
                    def k8sNamespace = "preprod-platform"

                    // Si on build depuis la branche principale (main), on déploie en PROD
                    if (env.BRANCH_NAME == 'main') {
                        envName = "prod"
                        k8sNamespace = "prod-platform"
                    }

                    echo "🚀 Déploiement via Helm en cours... Env: ${envName}, Namespace: ${k8sNamespace}"

                    // --- COMMANDES DE DÉPLOIEMENT HELM ---
                    // --create-namespace : gère la création automatique du namespace si besoin
                    // --kubeconfig : conserve ton accès sécurisé à K3s
                    sh """
                    helm upgrade --install app-products ./app-products/chart \
                      --namespace ${k8sNamespace} --create-namespace \
                      --kubeconfig=/root/.kube/config \
                      -f ./app-products/chart/values-${envName}.yaml \
                      --set image.tag=${IMAGE_TAG}

                    helm upgrade --install app-users ./app-users/chart \
                      --namespace ${k8sNamespace} \
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
            echo 'Pipeline termine avec succes - deploye via Helm sur k3s'
        }

        failure {
            echo 'Pipeline echoue'
        }
    }
}