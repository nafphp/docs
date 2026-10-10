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

## Package chapter outline

Package chapters follow one outline so readers find the same information in the same place.
Omit a section that has nothing to say; do not reorder the ones that remain.

1. A one-paragraph summary: what the package does and what it leaves to the application.
2. The "Required packages" box, generated from the page's `requires:` front matter.
3. A quick start: the smallest complete, copyable example and its expected result.
4. Concepts and tasks as H2 sections, each with an example.
5. Configuration: a table of every key with its full colon path, type, default and effect.
6. API details: helpers and classes with their signatures; link the function index.
7. "If the result is different": a symptom → check table.
8. Related pages.

Version history ("since 0.2.x", older starters, removed workarounds) goes into a collapsed
`??? note` box at the end of the page or section. Keep a short minimum-version statement
beside a feature when readers on the current starter lock need it to succeed.

## Formatting patterns

- **Content tabs** (`=== "Label"`) for genuine alternatives: macOS/Linux and Windows
  commands, database drivers, web servers. Never put file-titled blocks inside tabs; the
  example runner only reads blocks that start at the line's beginning.
- **Expected output** follows a command as a `text` block introduced by "Expected output:".
  Do not give output blocks a title; titles are reserved for files.
- **Admonitions** for security requirements (`warning`), destructive commands (`danger`),
  version notes (collapsed `??? note`) and short side remarks (`note`). Keep the main
  procedure outside them.
- **Code annotations** (`# (1)!` with a numbered list after the block) explain individual
  lines when a paragraph after the block would have to repeat the code.
- **Line highlighting** (`hl_lines="3 4"`) marks the lines that changed when a page extends a
  file the reader created earlier.
- **Diagrams** use Mermaid fences (```` ```mermaid ````). Describe the diagram's message in
  the surrounding text as well, so the page works without it.
- **Screenshots** show browser UI only; terminal output is copyable text instead. Generate
  them with `tools/capture_screenshots.py`, store them under `pages/assets/screenshots/`,
  give every image alt text that states what the reader should notice, and add the
  `screenshot` class for the frame.
- **Link text** names the target ("Forms and validation"), never "here" or "Behavior".

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
