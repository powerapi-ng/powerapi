# Contributing to PowerAPI

Thank you for your interest in contributing to PowerAPI! There are multiple ways to contribute, and we appreciate all contributions.

# Ways to contribute

We actively welcome any kind of contributions! Whether this contribution is: 

- Bug report
- Documentation writing
- Suggestion for improvement (new feature, code improvement, ...), implemented or not
- Test improvement
- Discussion on current issues
- Fix for an existing issue
- ...

Feel free to propose your contribution! 

# Licensing

All contributions should be under the same [BSD 3](https://choosealicense.com/licenses/bsd-3-clause/) licence that covers the project.

# Contribution workflow

We use pull requests to manage any change to the codebase. Please try to make your pull request as "atomic" as possible (related to one issue).
If you want to contribute to several issues or propose several distinct contributions, please create several pull requests to ease the review process.
If you want to propose a codebase modification, you should:

1. Fork the repository and create your branch from the pre-release branch
2. Write new tests if your modifications are not covered by existing tests and should be tested. In particular, if your contribution is a bug fix that have not been detected by existing tests,
add a test to ensure that this issue will not reappear later.
3. If you've modified the API or made any structural change in the architecture, update the documentation
4. Ensure that tests passes and your code lint (using pylint and flake8)
5. Issue a pull requests on the pre-release branch. This way your modifications will be included in the next stable release (available on master).

Each pull request have to be reviewed before beeing accepted. Some modifications can be
asked by the projet's maintainers.

## Bug report

If you are working with PowerAPI and you encounter a bug, please let us know.
You are welcome to submit an issue. This issue should describe the bug and it context with a
small test or a code snippet that reproduce the issue.

Great, easy to understand, bug reports often include:
- A quick summary of the issue 
- What was expected and what happened
- Step to reproduce
- Details on your execution environment:
  - Power API version
  - OS, kernel and CPU versions
- Optional notes on what you tried to solve the issue, guess on what may be wrong...

## Bug Fixes

If you are interested to contribute to PowerAPI you can fixes reported bugs.
They are listed in the issues with the label _bug_

Your pull request should contain a test that reproduce the bug, if the test do
not already exist, and the bug fix.
Please submit one pull request for each bug fix.

# PowerAPI codebase

## Coding style

We use `pylint` and `flake8` as linter to enforce rules on the coding style. Please validate your contributions using those tools to ease the validation process.

## Testing

We use `pytest` to test that PowerAPI works as expected and to avoid regressions. Feel free to add new tests to improve code coverage!
