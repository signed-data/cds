# TODO

## CDS Architecture Enhancement & Implementation Plan

#### 1. Clarify and Unify Layer Definitions
- **Action:** Define "Linked Data" as a formal 5th architectural layer or clarify its status in both the diagram and description.
- **Action:** Explicitly document the "MCP layer" as optional, specify its standard interface (input, output, verification), and provide deployment guidance.

#### 2. Detailed Component Implementation
###### Ingestor
- **Action:** Add detailed examples for domain-specific ingestors, including configuration, source onboarding, and error handling.
- **Action:** Specify required interfaces for LLM vs rule-based summarization with pluggable strategies.
- **Action:** Document configuration for private key management.

###### Transport/Store
- **Action:** Provide implementation details, code samples, and configuration for each supported backend (S3, SQS, EventBridge, HTTP, triplestore, etc.).
- **Action:** Include triple store schema mapping and transformation steps.

###### Consumer
- **Action:** Expand on verification (including error handling, support in multiple languages, integration strategies).
- **Action:** Document how consumers should fetch and refresh the public key.

###### Linked Data Layer
- **Action:** Publish complete documentation for all referenced vocabularies, context files, and domain schema URLs.
- **Action:** Specify versioning and deprecation policies for vocab/context.

#### 3. Security & Key Management
- **Action:** Document the process for onboarding new issuers, revoking or updating keys, and responding to key compromise.
- **Action:** Specify requirements for private key storage, rotation, and audit trails.

#### 4. Domain and Event Definition
- **Action:** Document domain payload schema definition process, validation requirements, and versioning.
- **Action:** Specify the complete process for registering and onboarding new data sources, including JSON-LD structure for `/sources/{id}`.
- **Action:** Provide validation tooling/examples for ensuring schema conformance.

#### 5. Operationalization & Deployment
- **Action:** Add instructions for alternative deployments (GCP, on-prem, single-node) in addition to AWS.
- **Action:** Provide local development and test environment setup documentation, including test data and mock services.

#### 6. Testing, Monitoring & CI/CD
- **Action:** Specify recommended test coverage, including signature verification, schema validation, and data integrity.
- **Action:** Document monitoring strategies for all layers: ingestion errors, signature failures, transport errors, etc.
- **Action:** Document recovery patterns for failures (retries, idempotency, DLQs).
- **Action:** Outline CI/CD practices and provide example GitHub Actions workflows for linting, testing, building, and deploying core components.

## Content Types Documentation Integrity Review Plan

#### Goal
Ensure `docs/content-types.md` is free of broken links, ambiguous instructions, and inconsistencies, making it fully reliable for contributors and users.

---

#### Review Steps

###### 1. Preliminary Checks
- [ ] Verify file loads and displays properly in GitHub and Markdown editors.
- [ ] Ensure table of contents (if present) matches the main body sections.

###### 2. Link Validation
######## A. Internal Links
- [ ] Check all relative links (e.g., `[CONTRIBUTING.md](../CONTRIBUTING.md)`) point to existing files in the repository.
- [ ] Validate anchor links within the document (if any) jump to the correct section headings.

######## B. External Links
- [ ] Test all `https://signed-data.org/vocab/...` URIs, ensuring they resolve and provide JSON-LD as described.
    - If links are examples only, clarify this in the documentation.
- [ ] Confirm all third-party references (if any) are up to date and not 404.

###### 3. Content Consistency
- [ ] Review slug transformation rules for conflicts or unclear instructions.
- [ ] Check that all Python and TypeScript code samples use the same logic as described in the narrative text.
- [ ] Ensure all examples under each section are correctly following the stated conventions.

###### 4. Accuracy and Clarity
- [ ] Locate and fix ambiguous or contradictory statements.
- [ ] Improve documentation for unclear processes, such as registration of new types.

###### 5. Cross-Referencing
- [ ] Ensure referenced files, such as `spec/domains/{domain}.md` and `vocab/domains/{domain}.jsonld`, exist, or add guidance on their creation.

###### 6. Final Review
- [ ] Perform a final manual read-through for typos, grammatical errors, and formatting issues.
- [ ] If automated documentation linters are in use (e.g., Markdownlint), ensure the file passes required checks.

---

#### Deliverables
- Checklist of all verified links with results.
- List of inconsistencies or problems found.
- Summary of recommended fixes.

---

#### Timeline
- **1:** Run automated and manual link checks, report results.
- **2:** Review content consistency and clarity, report issues.
- **3:** Summarize findings, create issues or PRs with proposed fixes.

---

#### Notes
- If certain `signed-data.org` links are intentional stubs or placeholders, mark them as such for users.
- This plan is iterative and can be repeated for future documentation changes.
