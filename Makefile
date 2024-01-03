.PHONY: git-hooks
git-hooks: .git/hooks/pre-commit .git/hooks/commit-msg

.git/hooks/%:
	@pre-commit install --hook-type $*
