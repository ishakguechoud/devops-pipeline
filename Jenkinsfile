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
                    echo "🔑 Configuration de HashiCorp Vault pour ${ENV_NAME} via API HTTP (Curl)..."
                    
                    sh """
                    # 1. Activation du moteur de secrets kv-v2 (on ignore si déjà actif)
                    curl --header "X-Vault-Token: \$INTERNAL_VAULT_TOKEN" \
                         --request POST \
                         --data '{"type": "kv", "options": {"version": "2"}}' \
                         ${VAULT_ADDR}/v1/sys/mounts/secret || true

                    # 2. Injection du secret (Corrigé sans le double 'data/data')
                    curl --header "X-Vault-Token: \$INTERNAL_VAULT_TOKEN" \
                         --request POST \
                         --data '{"data": {"keycloak-client-secret": "une_cle_secrete_super_secure"}}' \
                         ${VAULT_ADDR}/v1/secret/data/frontend

                    # 3. Réinitialisation de l'authentification Kubernetes
                    curl --header "X-Vault-Token: \$INTERNAL_VAULT_TOKEN" \
                         --request DELETE \
                         ${VAULT_ADDR}/v1/sys/auth/kubernetes || true

                    curl --header "X-Vault-Token: \$INTERNAL_VAULT_TOKEN" \
                         --request POST \
                         --data '{"type": "kubernetes"}' \
                         ${VAULT_ADDR}/v1/sys/auth/kubernetes

                    # 4. Liaison avec le cluster K3s local (avec bypass strict des validations temporelles d'émetteur)
                    curl --header "X-Vault-Token: \$INTERNAL_VAULT_TOKEN" \
                         --request POST \
                         --data '{
                           "kubernetes_host": "https://kubernetes.default.svc:443",
                           "disable_iss_validation": true,
                           "disable_local_ca_jwt": true
                         }' \
                         ${VAULT_ADDR}/v1/auth/kubernetes/config

                    # 5. Création de la politique d'accès (Policy)
                    curl --header "X-Vault-Token: \$INTERNAL_VAULT_TOKEN" \
                         --request PUT \
                         --data '{
                           "policy": "path \\"secret/data/frontend\\" { capabilities = [\\"read\\"] }"
                         }' \
                         ${VAULT_ADDR}/v1/sys/policies/acl/frontend-policy

                    # 6. Création du rôle Kubernetes pour l'application avec audience en format String
                    curl --header "X-Vault-Token: \$INTERNAL_VAULT_TOKEN" \
                         --request POST \
                         --data '{
                           "bound_service_account_names": ["frontend-sa"],
                           "bound_service_account_namespaces": ["preprod-platform", "prod-platform"],
                           "policies": ["frontend-policy"],
                           "audience": "https://kubernetes.default.svc.cluster.local",
                           "ttl": "24h"
                         }' \
                         ${VAULT_ADDR}/v1/auth/kubernetes/role/frontend-role
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