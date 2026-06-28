pipeline {
    agent any

    triggers {
        pollSCM('H/2 * * * *')
    }

    environment {
        NEXUS_URL = '192.168.74.128:8082'
        // Format de la date : AnnéeMoisJour-HeureMinute (ex: 20260628-1055)
        BUILD_TIMESTAMP = "${currentBuild.startTimeInMillis ? new Date(currentBuild.startTimeInMillis).format('yyyyMMdd-HHmm') : ''}"
        
        // Initialisation des variables globales (seront écrasées dans le premier stage)
        ENV_NAME = 'preprod'
        K8S_NAMESPACE = 'preprod-platform'
        SHORT_TAG = ''
    }

    stages {
        stage('Initialize Env & Tags') {
            steps {
                script {
                    // 1. Détermination de l'environnement selon la branche
                    if (env.GIT_BRANCH == 'origin/main' || env.GIT_BRANCH == 'main') {
                        ENV_NAME = "prod"
                        K8S_NAMESPACE = "prod-platform"
                    }

                    // 2. Création du tag sans le préfixe d'application (ex: Application5-20260628-1055)
                    SHORT_TAG = "Application${BUILD_NUMBER}-${BUILD_TIMESTAMP}"

                    echo "🌿 Branche détectée : ${env.GIT_BRANCH}"
                    echo "🚀 Environnement cible : ${ENV_NAME.toUpperCase()}"
                    echo "📁 Sous-dossier Nexus : /v2/app-xxxx/${ENV_NAME}/"
                    echo "🏷️ Tag final de l'image : ${SHORT_TAG}"
                }
            }
        }

        stage('Build Images') {
            steps {
                // L'astuce est ici : ajouter /${ENV_NAME} crée le sous-dossier automatiquement dans Nexus
                sh "docker build -t ${NEXUS_URL}/app-users/${ENV_NAME}:${SHORT_TAG} ./app-users"
                sh "docker build -t ${NEXUS_URL}/app-products/${ENV_NAME}:${SHORT_TAG} ./app-products"
                sh "docker build -t ${NEXUS_URL}/app-frontend/${ENV_NAME}:${SHORT_TAG} ./app-frontend"
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

                    docker push ${NEXUS_URL}/app-users/${ENV_NAME}:${SHORT_TAG}
                    docker push ${NEXUS_URL}/app-products/${ENV_NAME}:${SHORT_TAG}
                    docker push ${NEXUS_URL}/app-frontend/${ENV_NAME}:${SHORT_TAG}
                    """
                }
            }
        }

        stage('Deploy via Helm') {
            steps {
                script {
                    echo "📦 Déploiement Helm dans le Namespace : ${K8S_NAMESPACE}"

                    sh """
                    helm upgrade --install app-products ./app-products/chart \
                      --namespace ${K8S_NAMESPACE} --create-namespace \
                      --kubeconfig=/root/.kube/config \
                      -f ./app-products/chart/values-${ENV_NAME}.yaml \
                      --set image.tag=${SHORT_TAG}

                    helm upgrade --install app-users ./app-users/chart \
                      --namespace ${K8S_NAMESPACE} --create-namespace \
                      --kubeconfig=/root/.kube/config \
                      -f ./app-users/chart/values-${ENV_NAME}.yaml \
                      --set image.tag=${SHORT_TAG}

                    helm upgrade --install app-frontend ./app-frontend/chart \
                      --namespace ${K8S_NAMESPACE} --create-namespace \
                      --kubeconfig=/root/.kube/config \
                      -f ./app-frontend/chart/values-${ENV_NAME}.yaml \
                      --set image.tag=${SHORT_TAG}
                    """
                }
            }
        }
    }

    post {
        success {
            echo "✅ Pipeline terminé avec succès — trié dans le dossier [${ENV_NAME.toUpperCase()}] sur Nexus"
        }
        failure {
            echo '❌ Pipeline échoué — vérifier les logs ci-dessus'
        }
    }
}