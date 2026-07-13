# AI integration plan

## Goal

Prepare the current architecture for future AI features without introducing a large new framework. The main principle is to keep AI work as optional analysis plugins that operate on the same listing data already handled by collectors and the existing scoring pipeline.

## Suggested extension points

### 1. OCR
- Extension point: a lightweight analysis plugin that consumes images or image URLs.
- Input: image bytes or a URL already attached to a listing.
- Output: OCR text stored in the analysis artifacts payload.
- Integration: run after a listing has been normalized and before the final opportunity evaluation.
- Plugin boundary: implement as an optional plugin in the analysis package with no change to collector contracts.

### 2. Image classification
- Extension point: another optional plugin that attaches labels to the listing.
- Input: image data or derived metadata from the image model.
- Output: a list of labels such as "electronics", "gaming", "damage".
- Integration: enrich the existing listing context and feed the results into flip scoring or downstream rules.
- Plugin boundary: keep it side-effect free and return structured outputs rather than mutating the database layer.

### 3. Object detection
- Extension point: an analysis plugin that identifies visible objects or defects.
- Input: image data plus optional OCR context.
- Output: detected objects, defect tags, and confidence values.
- Integration: use the results to strengthen existing repair indicators and support downstream duplicate or quality checks.
- Plugin boundary: expose a simple interface that returns a normalized list of detected items.

### 4. Sentence embeddings
- Extension point: an analysis plugin that converts title and description text into vector embeddings.
- Input: listing text only.
- Output: embedding vectors and a similarity score.
- Integration: use them for duplicate detection and recommendation matching without changing the persistence model.
- Plugin boundary: store embeddings as optional analysis artifacts or in a future table; keep the core listing model unchanged for now.

### 5. Local LLM analysis
- Extension point: an optional plugin that summarizes listing content or explains an opportunity.
- Input: title, description, OCR text, and any extracted labels.
- Output: summary, risk notes, and a structured explanation string.
- Integration: run after text extraction and classification to provide human-readable insight.
- Plugin boundary: keep the model call behind a thin adapter so different backends can be swapped later.

### 6. Price prediction
- Extension point: a prediction plugin that estimates resale value.
- Input: title, category, brand, condition notes, and historical price data.
- Output: predicted price or confidence interval.
- Integration: feed the result into the existing FlipScore rules or into a future opportunity service.
- Plugin boundary: return a prediction object rather than directly writing to the database.

### 7. Duplicate detection
- Extension point: an analysis plugin that compares a listing against existing listings.
- Input: text, embeddings, source, and external identifier.
- Output: duplicate score and candidate matches.
- Integration: operate on the repository layer, but keep the comparison logic outside the persistence models.
- Plugin boundary: expose a simple matcher interface that can use exact matching first and embeddings later.

### 8. Recommendation engine
- Extension point: a plugin or service that ranks listings for the user or for a workflow.
- Input: current listing context, past purchases, and similarity signals.
- Output: recommendation reason and score.
- Integration: compose the recommendation from existing analysis artifacts and repository data; no change is required to the collector interface.
- Plugin boundary: keep the ranking strategy separate from the persistence layer and make it a pure service over existing data.

## Suggested interfaces

### Core interface
- A minimal protocol such as AIPlugin with a run(context, artifacts) method.
- A shared ListingContext carrying the basic fields already known to collectors.
- A shared AnalysisArtifacts container for optional outputs.

### Why this fits the existing architecture
- Collectors already normalize listings into a consistent shape.
- Analysis modules already contain scoring logic and can naturally host AI-based enrichment.
- The database layer already separates persistence from business rules, so AI outputs can remain optional and non-blocking.

## Recommended plugin boundaries

1. Collector boundary
- Keep collectors focused on fetching and normalization.
- Do not let collectors directly depend on OCR or LLM packages.

2. Analysis boundary
- Place AI-related logic in analysis/ as plugins.
- Each plugin should accept a ListingContext and return AnalysisArtifacts.

3. Repository boundary
- Persist only the final results needed for the product experience, such as summaries, scores, or derived flags.
- Avoid storing raw model outputs unless they are explicitly needed.

4. Application boundary
- Wire the plugins from the existing application entry points or from a future orchestration service.
- The main application should not need to know which plugin is used internally.

## Minimal integration pattern

1. A collector normalizes a listing.
2. The listing is converted to ListingContext.
3. Optional plugins run in sequence and populate AnalysisArtifacts.
4. Existing scoring and repository logic consume the enriched artifacts.
5. If a plugin is unavailable or fails, the system falls back to the current non-AI behavior.

## Design principles

- Prefer small, composable plugins over a monolithic AI service.
- Keep the runtime contract simple and dependency-light.
- Make AI features opt-in and non-blocking.
- Preserve the current architecture by adding capabilities around the existing analysis and persistence seams.
