---
name: toc-extractor
description: >-
  Extracts Table of Contents from an image using AI vision, translates non-English chapter titles to English with user confirmation, and outputs structured toc.json with page boundaries.
---

# ToC Extractor

## Overview

The `toc-extractor` skill processes Table of Contents (ToC) images, extracts chapter metadata and page numbers using AI vision, provides rough English translations for any non-English titles, asks for user confirmation in chat, and saves the verified results into a clean `toc.json` file.

---

## Output Format (`toc.json`)

The output JSON file follows this structure:

```json
{
  "title": "Table of Contents",
  "chapters": [
    {
      "id": "c001",
      "chapter": "CH 1",
      "original_title": "Original Title (or same as title if English)",
      "title": "Confirmed English Title",
      "start_page": 7,
      "end_page": 30
    }
  ]
}
```

---

## Step-by-Step Workflow

### 1. Visual Inspection & Extraction
- Analyze the provided ToC image file or image attachment.
- Read all visible chapters, section headers (e.g. `CH 1`, `CH 2`, `FINALE`, `AFTERWORD`), titles, and starting page numbers.

### 2. ID & Page Range Calculation
- Generate standardized `id` tags (e.g. `c001`, `c002`, `finale`, `appendix`, `afterword`, `epilogue`).
- Calculate each chapter's `end_page` as `(next_chapter.start_page - 1)`.
- If the final section has no explicit end page, set `"end_page": null`.

### 3. Translation & Draft Presentation (Mandatory Chat Step)
- If titles are in a non-English language:
  - Generate a rough, contextually accurate English translation.
  - Set `"original_title"` to the exact text in the image.
  - Set `"title"` to the proposed English translation.
- If titles are already in English:
  - Keep `"original_title"` and `"title"` identical.
- **Present the complete draft table to the user in chat:**

  ```markdown
  ### Table of Contents Extraction Draft

  | Chapter | Original Title | Proposed English Title | Start Page | End Page |
  | :--- | :--- | :--- | :--- | :--- |
  | CH 1 | ... | ... | 7 | 30 |

  Please confirm if the extraction and translations look good, or let me know any edits to make before I generate `toc.json`.
  ```

### 4. File Creation (`toc.json`)
- **WAIT** for explicit user confirmation in chat.
- Once confirmed or edited by the user, write the finalized JSON to `toc.json` in the active project directory (or specified path).

---

## Common Pitfalls & Handling

- **Textured or Faint Backgrounds**: Read faint watermarks or background text carefully to avoid confusing background graphic elements with chapter titles.
- **Unnumbered Titles**: For sections without explicit chapter numbers (e.g., `FINALE`, `AFTERWORD`, `EPILOGUE`), assign descriptive IDs like `finale`, `afterword`, `epilogue`.
- **Skipping Confirmation**: Never generate `toc.json` automatically without first presenting the draft table and translations to the user for approval.
