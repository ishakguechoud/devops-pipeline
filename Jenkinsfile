pipeline {
    agent any

    triggers {
        pollSCM('H/2 * * * *')
    }

    environment {
        NEXUS_URL = '192.168.74.128:8082'
        BUILD_TIMESTAMP = "${currentBuild.startTimeInMillis ? new Date(currentBuild.startTimeInMillis).format('yyyyMMdd-HHmm') : ''}"
        PROJECT_NAME = 'workflow-devops'
        
        ENV_NAME = 'preprod'
        K8S_NAMESPACE = 'preprod-platform'
        SHORT_TAG = ''
        
        // 🔐 URL d'accès à ton Vault pour le CLI dans le pipeline
        VAULT_ADDR = 'http://192.168.74.128:30200' 
    }

    stages {
        stage('Initialize Env & Tags') {
            steps {
                script {
                    if (env.GIT_BRANCH == 'origin/main' || env.GIT_BRANCH == 'main') {
                        ENV_NAME = "prod"
                        K8S_NAMESPACE = "prod-platform"
                    }

                    SHORT_TAG = "Application${BUILD_NUMBER}-${BUILD_TIMESTAMP}"

                    echo "🌿 Branche détectée : ${env.GIT_BRANCH}"
                    echo "📦 Projet : ${PROJECT_NAME}"
                    echo "🚀 Environnement : ${ENV_NAME.toUpperCase()}"
                    echo "🏷️ Tag de l'image : ${SHORT_TAG}"
                }
            }
        }

        stage('Build Images') {
            steps {
                sh "docker build -t ${NEXUS_URL}/${PROJECT_NAME}/${ENV_NAME}/app-users:${SHORT_TAG} ./app-users"
                sh "docker build -t ${NEXUS_URL}/${PROJECT_NAME}/${ENV_NAME}/app-products:${SHORT_TAG} ./app-products"
                sh "docker build -t ${NEXUS_URL}/${PROJECT_NAME}/${ENV_NAME}/app-frontend:${SHORT_TAG} ./app-frontend"
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

                    docker push ${NEXUS_URL}/${PROJECT_NAME}/${ENV_NAME}/app-users:${SHORT_TAG}
                    docker push ${NEXUS_URL}/${PROJECT_NAME}/${ENV_NAME}/app-products:${SHORT_TAG}
                    docker push ${NEXUS_URL}/${PROJECT_NAME}/${ENV_NAME}/app-frontend:${SHORT_TAG}
                    """
                }
            }
        }

    stage('Configure Vault') {
            steps {
                withCredentials([string(credentialsId: 'vault-token', variable: 'INTERNAL_VAULT_TOKEN')]) {
                    echo "🔑 Configuration de HashiCorp Vault pour ${ENV_NAME}..."
                    
                    // On lance le conteneur en arrière-plan, on exécute les commandes dedans via docker exec, puis on le nettoie.
                    // Cette approche élimine TOUS les problèmes d'échappement de caractères de Jenkins.
                    sh """
                    # 1. Démarrage d'un conteneur temporaire Vault en mode interactif/détaché
                    docker run -d --name vault-cli-agent -e VAULT_ADDR=${VAULT_ADDR} -e VAULT_TOKEN=\$INTERNAL_VAULT_TOKEN hashicorp/vault:2.0.2 sleep 300
                    
                    # 2. Exécution des configurations à l'intérieur du conteneur
                    docker exec vault-cli-agent vault secrets enable -path=secret kv-v2 || true
                    
                    # Injection du secret au bon chemin (sans double data)
                    docker exec vault-cli-agent vault kv put secret/frontend keycloak-client-secret="une_cle_secrete_super_secure" || true
                    
                    # Réinitialisation de l'auth Kubernetes
                    docker exec vault-cli-agent vault auth disable kubernetes || true
                    docker exec vault-cli-agent vault auth enable kubernetes
                    
                    # Liaison avec le cluster K3s (avec le bon issuer et le CA local du pod)
                    docker exec vault-cli-agent vault write auth/kubernetes/config \
                        kubernetes_host="https://kubernetes.default.svc:443" \
                        kubernetes_ca_cert="/var/run/secrets/kubernetes.io/serviceaccount/ca.crt" \
                        issuer="https://kubernetes.default.svc.cluster.local" \
                        disable_iss_validation=false
                    
                    # Injection de la politique via une commande heredoc exécutée dans le conteneur
                    docker exec -i vault-cli-agent sh -c 'vault policy write frontend-policy -' <<EOF
path "secret/data/frontend" {
  capabilities = ["read"]
}
EOF

                    # Configuration du rôle Kubernetes avec audience vide
                    docker exec vault-cli-agent vault write auth/kubernetes/role/frontend-role \
                        bound_service_account_names="frontend-sa" \
                        bound_service_account_namespaces="preprod-platform,prod-platform" \
                        policies="frontend-policy" \
                        audience="" \
                        ttl="24h"
                    
                    # 3. Nettoyage du conteneur temporaire
                    docker rm -f vault-cli-agent
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
            echo "✅ Pipeline réussi ! Images stockées dans : ${PROJECT_NAME}/${ENV_NAME}/"
        }
        failure {
            echo '❌ Pipeline échoué'
        }
    }
}