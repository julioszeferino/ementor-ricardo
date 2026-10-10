#!/usr/bin/env bash
# Aplica os guardrails do repositório no GitHub (rodar pelo MENTOR, que é admin).
#
#   ./scripts/setup_github_guardrails.sh                 # só protege a master
#   ./scripts/setup_github_guardrails.sh <usuario-github> # também convida o mentorado
#
# Resultado:
#   - ninguém além do admin faz push direto na master (nem force-push, nem delete);
#   - merge só via PR, com 1 aprovação do CODEOWNER (o mentor) e CI verde;
#   - aprovações caem se novos commits forem enviados depois da revisão.
#
# Requisitos: gh autenticado como admin do repo. Em repositório PRIVADO a proteção de
# branch exige GitHub Pro/Team; no plano Free só funciona com o repositório público.
set -euo pipefail

REPO="${REPO:-$(gh repo view --json nameWithOwner --jq .nameWithOwner)}"
BRANCH="${BRANCH:-master}"
MENTEE="${1:-}"

# Devem bater com os nomes dos jobs em .github/workflows/ci.yml
REQUIRED_CHECKS='["lint", "test", "dbt", "airflow-dags", "secrets"]'

echo "==> Configurando merges em ${REPO} (squash only, apaga branch após merge)"
gh repo edit "${REPO}" \
  --enable-squash-merge \
  --enable-merge-commit=false \
  --enable-rebase-merge=false \
  --delete-branch-on-merge

echo "==> Protegendo a branch ${BRANCH}"
gh api --method PUT "repos/${REPO}/branches/${BRANCH}/protection" \
  -H "Accept: application/vnd.github+json" \
  --input - <<JSON
{
  "required_status_checks": {
    "strict": true,
    "contexts": ${REQUIRED_CHECKS}
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "require_code_owner_reviews": true,
    "dismiss_stale_reviews": true,
    "require_last_push_approval": true
  },
  "restrictions": null,
  "required_linear_history": true,
  "required_conversation_resolution": true,
  "allow_force_pushes": false,
  "allow_deletions": false
}
JSON

if [[ -n "${MENTEE}" ]]; then
  echo "==> Convidando ${MENTEE} como colaborador"
  gh api --method PUT "repos/${REPO}/collaborators/${MENTEE}" --silent
fi

echo "==> Proteção atual:"
gh api "repos/${REPO}/branches/${BRANCH}/protection" \
  --jq '{checks: .required_status_checks.contexts,
         approvals: .required_pull_request_reviews.required_approving_review_count,
         code_owners: .required_pull_request_reviews.require_code_owner_reviews,
         force_push: .allow_force_pushes.enabled}'
