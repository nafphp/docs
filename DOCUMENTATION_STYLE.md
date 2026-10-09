# Writing NAF documentation

Write for developers who know PHP and Composer but are new to NAF. Explain conventions and
observable behavior. The published packages are the API authority.

## Language

Use clear English, active sentences and sentence case for headings. Address readers directly
when giving instructions. Name the subject: "Database access", "Register a command" or
"OAuth authorization server". Use the same terms in navigation and page titles.

Describe behavior before design rationale. Replace slogans, metaphors and conversational
asides with facts. Avoid "just", "obviously", "you are done", "nothing to learn" and "the
whole integration". Do not claim something is a common mistake without evidence. Explain
limitations with the affected feature and the action the reader needs.

Describe the current design. Previous drafts and possible future features belong in issues
or design proposals. "Returns null" or "throws DatabaseException" is more useful than
"handles errors". Preserve technical qualifications when simplifying language.

## Support the reader

Begin tutorials with the result the reader will build, then explain the starting project and
prerequisites. Give one recommended first path; offer alternatives by their purpose. Keep
older-version notes and optional cleanup in clearly labelled sections or collapsed details
so they do not interrupt the main exercise. Keep requirements that affect the next step visible.

Connect steps by explaining what is now in place and what the next file adds. Describe these
intermediate states accurately: registering a route does not mean the application works before
its controller and template exist. End the exercise with an observable result and a next step.

Use a calm, respectful tone. Explain a restriction's reason and the reader's next action.
Avoid blame, exaggerated reassurance and promises about how quickly someone will finish.
Friendliness comes from useful guidance, rather than jokes or repeated congratulations.

Add a short "If the result is different" section near verification. Pair a recognizable symptom
with a specific check or recovery step, and link to deeper troubleshooting when useful.
Distinguish expected validation responses from application failures. Keep security requirements
explicit; do not suggest disabling protection to make an example work.

## Page purpose

| Type | Reader's goal | Required content |
|---|---|---|
| Tutorial | Build a first working application | Starting state, ordered steps, complete files and expected results |
| Task guide | Complete a specific task | Prerequisites, file locations, procedure, verification and failure cases |
| Reference | Look up behavior | Inputs, return values, defaults, exceptions, side effects and version limits |
| Explanation | Understand a mechanism | Responsibilities, execution order, relationships and tradeoffs |

A plugin chapter can combine setup and reference, with descriptive headings. Link to related
material instead of repeating it. Split chapters when tasks need independent instructions.

## Examples and configuration

- State the starting application, packages, extensions and minimum versions.
- Name the file and say whether to create, replace or extend it.
- Reserve file titles on fenced blocks for complete files: the example runner copies them.
- Label fragments and name their context. Define classes used in runnable examples.
- Import functions explicitly and return PSR-7 responses from handlers.
- Reuse existing NAF services and interfaces; keep business rules in application services.
- Include observable success and relevant failure results.
- Use disposable storage and captured mail in tests.
- Describe configuration keys with their full path, type, default and effect.
- Distinguish required dependencies from optional integrations; use environment values for secrets.

Reference fragments can omit unrelated setup, but must explain what they assume. Do not
present an unsafe example and rely on a later warning to correct it.

## Review and publication

Compare related chapters for contradictions. Follow helpers through services, bootstrap and
tests, and confirm the published version includes the behavior. Preserve page URLs and useful
heading anchors. Change generated references through their generator.

Follow [README.md](README.md) for checks, including verification of new examples. Review rendered
pages for outline, code, tables and links. Complete the merge and deployment verification in
[AGENT_WORKFLOW.md](AGENT_WORKFLOW.md).
