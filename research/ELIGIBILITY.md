# Eligibility check, 2026-10-01 UTC

Decision: proceed with an original mechanism replication. No usable GitHub implementation of **this paper** was found in the bounded search. Confidence: moderate. This is not a universal absence claim or a claim to be first.

Paper: Isham Kalappurackal Mansoor, Abhishek Phadke, Pratip Rana, [Verified Tool Calls Improve LLM Agent Reliability Under Non-Atomic Failures](https://arxiv.org/abs/2608.02645), arXiv:2608.02645v1. First submission: 2026-07-31 16:16:14 UTC, inside the six calendar months preceding 2026-10-01 (2026-04-01 onward). The PDF title-page date (August 5) and HTML document header (August 24) are not first submission dates. arXiv lists CC BY 4.0.

Read all 12 PDF pages; PDF, full HTML and extracted text are retained only in the private reviewer archive, excluded from this public checkout. Use the official [PDF](https://arxiv.org/pdf/2608.02645v1) and [HTML](https://arxiv.org/html/2608.02645v1) for public source access. Algorithm 1 checked against PDF page 7 as well as HTML. No implementation link in the paper text was found. The HTML viewer's GitHub issue link is a rendering feedback link, not paper code.

## Search record

| Check | Query / URL | Observation |
|---|---|---|
| Web exact title | Full title + `github`; full title phrase restricted to `site:github.com` | Paper, discussion, lesson/reference hits; no usable reproduction located |
| Web ID | `"2608.02645" github`, then `site:github.com` | References in notes and discussion, not implementation |
| GitHub repository API | `https://api.github.com/search/repositories?q=2608.02645` | HTTP 200, total_count 0; raw JSON retained |
| GitHub full title API | Full quoted title in repository search | HTTP 200, total_count 0; raw JSON retained |
| GitHub shortened title API | `"Verified Tool Calls"` | 10 broad matches. Metadata screened; no paper reproduction identified. Most match generic tool validation, prompt testing or unrelated verification |
| Closest metadata hit | `MkaliezZ/dhms-engine` | README describes memory/context stability diagnosis and pre-execution assurance, not this paper's postcondition/retry experiment. Retained README; code not copied |
| Author profile and repos | `https://github.com/abhishekphadke`; public repos endpoint, per_page=100 | HTTP 200; 27 public repositories, none relevant by metadata. Fewer than page size, so listing complete at check time |
| Author official homepage | `https://sites.google.com/view/abhishek-phadke` | Identity/institution checked; no paper code link in accessible text |
| Other authors | Full author names + github; Pratip's ODU faculty page | No resolved public GitHub code link. Faculty `Git` goes to ODU infrastructure; these authors' private/unindexed repositories remain unknown |
| Reference-only hits | `iarechaga/oh-my-learning/.../07-designing-for-recoverable-failure.md`; `rush86999/atom/.../STANFORD_VIRTUAL_BIOTECH_PAPERCLIP.md` | Citation/lesson and architecture discussion; no faithful paper implementation in inspected material |
| Gist supplied by scout | `mpalpha/cd391ce91bdca79257089cc4a5ef0949` | Markdown-only governance spec, states it is not a code bundle; not an implementation of this paper |

Web GitHub search pages were blocked/unavailable; unauthenticated repository API reads subsequently succeeded. Anonymous GitHub code search was not available. Repo-name/description search does not cover all source files. No credentials changed, no author contacted, no packages installed. Private-archive search receipts (excluded here): downloaded profiles, `web-search-receipt.txt`, `download-log*.json`, full API JSON and third-party snapshots. Public search facts are `research/search-facts.json`; exact title/ID count JSON is included. Initial shell-network read failed; approved read-only network access retrieved public files. This does not weaken or bypass the user gate: any later discovery of usable paper code requires holding the project and reporting it.

## Material ambiguities to preserve

Algorithm 1 accepts SUCCESS immediately, does not verify definitive FAILURE, and at N=1 may send a retry then fall out without inspecting its response. Section 4.6 describes one retry; the pseudocode counts loop iterations, so UNKNOWN also spends its only iteration. The displayed Section 4.3 predicates omit welcome-message count and invoice-record status despite Section 4.2's task requirements. The key formula includes a timestamp bucket whose width and restart behavior are unspecified. Failure precedence, delays, server key semantics and actual API decomposition are not provided. Our assumptions must be explicit; local outcomes cannot reproduce the Gemini/LangGraph LLM percentages.

Public-release provenance note: downloaded paper/page/profile/API archives mentioned above remain in the separate private research checkout. Official paper links, `research/search-facts.json`, original eligibility notes and exact synthetic evaluation artifacts are included here. No unpublished article draft is included. The historical evaluated revisions are mapped by `RELEASE_PROVENANCE.json`; source hashes are byte-identical.
