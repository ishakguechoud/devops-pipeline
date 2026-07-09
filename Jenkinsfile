pipeline {
    agent any

    triggers {
        pollSCM('H/2 * * * *')
    }

    environment {
        NEXUS_URL = '192.168.74.128:8082'
        BUILD_TIMESTAMP = "${currentBuild.startTimeInMillis ? new Date(currentBuild.startTimeInMillis).format('yyyyMMdd-HHmm') : ''}"
        PROJECT_NAME = 'workflow-devops'
        VAULT_ADDR = 'http://192.168.74.128:30200'
    }

    stages { // <--- L'oubli était ici !

        stage('Initialize Env & Tags') {
            steps {
                script {
                    if (env.GIT_BRANCH == 'origin/main' || env.GIT_BRANCH == 'main') {
                        env.ENV_NAME = "prod"
                        env.K8S_NAMESPACE = "prod-platform"
                    } else {
                        env.ENV_NAME = "preprod"
                        env.K8S_NAMESPACE = "preprod-platform"
                    }

                    env.SHORT_TAG = "Application${BUILD_NUMBER}-${BUILD_TIMESTAMP}"

                    echo "🌿 Branche détectée : ${env.GIT_BRANCH}"
                    echo "📦 Projet : ${PROJECT_NAME}"
                    echo "🚀 Environnement : ${env.ENV_NAME.toUpperCase()}"
                    echo "📦 Namespace : ${env.K8S_NAMESPACE}"
                    echo "🏷️ Tag de l'image : ${env.SHORT_TAG}"
                }
            }
        }

        stage('Build Images') {
            steps {
                sh "docker build -t ${NEXUS_URL}/${PROJECT_NAME}/${ENV_NAME}/app-users:${SHORT_TAG} ./app-users"
                sh "docker build -t ${NEXUS_URL}/${PROJECT_NAME}/${ENV_NAME}/app-products:${SHORT_TAG} ./app-products"
                sh "docker build -t ${NEXUS_URL}/${PROJECT_NAME}/${ENV_NAME}/app-frontend:${SHORT_TAG} ./app-frontend"
                sh "docker build -t ${NEXUS_URL}/${PROJECT_NAME}/${ENV_NAME}/app-gateway:${SHORT_TAG} ./app-gateway"
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
                    docker push ${NEXUS_URL}/${PROJECT_NAME}/${ENV_NAME}/app-gateway:${SHORT_TAG}
                    """
                }
            }
        }

        stage('Configure Vault') {
            steps {
                withCredentials([string(credentialsId: 'vault-token', variable: 'INTERNAL_VAULT_TOKEN')]) {
                    echo "🔑 Configuration de HashiCorp Vault pour ${ENV_NAME} (idempotent, sans toucher aux secrets applicatifs)..."

                    sh """
                    # 1. Activation du moteur de secrets kv-v2 (ignoré si déjà actif)
                    curl --header "X-Vault-Token: \$INTERNAL_VAULT_TOKEN" \
                         --request POST \
                         --data '{"type": "kv", "options": {"version": "2"}}' \
                         ${VAULT_ADDR}/v1/sys/mounts/secret || true

                    # 2. Activation de l'auth kubernetes (ignoré si déjà actif)
                    curl --header "X-Vault-Token: \$INTERNAL_VAULT_TOKEN" \
                         --request POST \
                         --data '{"type": "kubernetes"}' \
                         ${VAULT_ADDR}/v1/sys/auth/kubernetes || true

                    # 3. Création / mise à jour de la policy
                    curl --header "X-Vault-Token: \$INTERNAL_VAULT_TOKEN" \
                         --request PUT \
                         --data '{
                           "policy": "path \\"secret/data/frontend\\" { capabilities = [\\"read\\"] }"
                         }' \
                         ${VAULT_ADDR}/v1/sys/policies/acl/frontend-policy

                    # 4. Création / mise à jour du rôle (SANS le champ audience)
                    curl --header "X-Vault-Token: \$INTERNAL_VAULT_TOKEN" \
                         --request POST \
                         --data '{
                           "bound_service_account_names": ["frontend-sa"],
                           "bound_service_account_namespaces": ["preprod-platform", "prod-platform"],
                           "policies": ["frontend-policy"],
                           "ttl": "24h"
                         }' \
                         ${VAULT_ADDR}/v1/auth/kubernetes/role/frontend-role
                    """
                }
            }
        }

        stage('Verify Vault Kubernetes Config') {
            steps {
                echo "🔍 Vérification que token_reviewer_jwt est bien configuré (sinon Vault Agent renvoie 403)..."
                sh """
                kubectl exec -n vault vault-0 --kubeconfig=/root/.kube/config -- sh -c \
                  'vault read -format=json auth/kubernetes/config' | grep -q '"token_reviewer_jwt_set":true' \
                  && echo "✅ token_reviewer_jwt correctement configuré" \
                  || echo "⚠️  ATTENTION : token_reviewer_jwt absent, l'auth Vault Agent va échouer. Configuration manuelle requise."
                """
            }
        }

        stage('Update Git for ArgoCD') {
            steps {
                script {
                    echo "📝 Injection du tag [${SHORT_TAG}] dans les fichiers de configuration de ${ENV_NAME}..."

                    // Utilisation de sed pour chercher la clé "tag:" et y injecter la version générée
                    sh """
                    sed -i 's/tag:.*/tag: "${SHORT_TAG}"/' ./app-products/chart/values-${ENV_NAME}.yaml
                    sed -i 's/tag:.*/tag: "${SHORT_TAG}"/' ./app-users/chart/values-${ENV_NAME}.yaml
                    sed -i 's/tag:.*/tag: "${SHORT_TAG}"/' ./app-frontend/chart/values-${ENV_NAME}.yaml
                    sed -i 's/tag:.*/tag: "${SHORT_TAG}"/' ./app-gateway/chart/values-${ENV_NAME}.yaml
                    """

                    echo "🚀 Envoi des modifications sur GitHub pour déclencher ArgoCD..."
                    // Remplace 'github-credentials' par l'ID exact de tes identifiants GitHub stockés dans Jenkins
                    withCredentials([usernamePassword(credentialsId: 'github-credentials', usernameVariable: 'GIT_USER', passwordVariable: 'GIT_TOKEN')]) {
                        
                        // Extraction propre du nom de la branche (pour enlever le préfixe origin/)
                        def branchName = env.GIT_BRANCH.replace('origin/', '')

                        sh """
                        git config user.email "jenkins-bot@zak-local.com"
                        git config user.name "Jenkins GitOps Bot"
                        
                        git add ./app-products/chart/values-${ENV_NAME}.yaml \
                                ./app-users/chart/values-${ENV_NAME}.yaml \
                                ./app-frontend/chart/values-${ENV_NAME}.yaml \
                                ./app-gateway/chart/values-${ENV_NAME}.yaml
                        
                        # Le [skip ci] évite que Jenkins ne boucle à l'infini en détectant son propre commit
                        git commit -m "[skip ci] chore(gitops): update ${ENV_NAME} image tags to ${SHORT_TAG}"                        
                        git push https://${GIT_USER}:${GIT_TOKEN}@github.com/ishakguechoud/devops-pipeline.git HEAD:${branchName}
                        """
                    }
                }
            }
        }
    } // Fin de STAGES

    post {
        success {
            echo "✅ Pipeline réussi ! Images stockées dans : ${PROJECT_NAME}/${ENV_NAME}/"
        }
        failure {
            echo '❌ Pipeline échoué'
        }
    }
}