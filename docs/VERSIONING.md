# Versioning and Changelog

This project uses [Semantic Versioning](https://semver.org/) for version numbering and [semantic-release](https://github.com/semantic-release/semantic-release) for automated versioning and changelog generation.

## Semantic Versioning

Semantic versioning follows the pattern: MAJOR.MINOR.PATCH

- **MAJOR** version when you make incompatible API changes
- **MINOR** version when you add functionality in a backward compatible manner
- **PATCH** version when you make backward compatible bug fixes

## Commit Message Format

This project uses conventional commits to automate the release process. The commit message should be structured as follows:

```
<type>(<scope>): <subject>
```

### Types

- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation only changes
- **style**: Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc)
- **refactor**: A code change that neither fixes a bug nor adds a feature
- **perf**: A code change that improves performance
- **test**: Adding missing tests or correcting existing tests
- **chore**: Changes to the build process or auxiliary tools and libraries such as documentation generation

### Scope

The scope is optional and can be anything specifying the place of the commit change, such as 'frontend', 'backend', 'api', etc.

### Subject

The subject contains a succinct description of the change:
- use the imperative, present tense: "change" not "changed" nor "changes"
- don't capitalize the first letter
- no dot (.) at the end

## Automated Versioning

Commits to the main branch trigger the semantic-release process:

1. Analyzes commits since last release to determine the next version number
2. Generates release notes from commit messages
3. Updates CHANGELOG.md
4. Creates a new GitHub release
5. Tags the commit with the new version

## Manual Releases

While the process is automated, you can manually create a release by:

1. Using conventional commits to properly describe your changes
2. Pushing to the main branch
3. Letting the CI/CD pipeline handle the rest

## Viewing the Changelog

The project changelog is maintained in the [CHANGELOG.md](../CHANGELOG.md) file at the root of the repository. 