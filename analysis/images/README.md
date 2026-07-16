# Image Analysis Architecture

This module provides a modular and extensible architecture for image analysis within MAIE.

## Core Components

- **`types.py`**: Defines common data structures like `BoundingBox`, `ImageDetection`, and `ImageAnalysisResult`.
- **`interfaces.py`**: Defines `Protocol` based interfaces for various image analysis tasks.
- **`pipeline.py`**: Orchestrates multiple analysis tasks and provides an `AIPlugin` compatible interface.

## Supported Analysis Tasks

The architecture currently supports the following interfaces:

1.  **`ImageOCR`**: Text extraction from images.
2.  **`ObjectDetector`**: Identifying and locating specific objects (e.g., "laptop", "scratch").
3.  **`ImageClassifier`**: High-level categorization of the image.
4.  **`BrandRecognizer`**: Detecting brand logos and names.
5.  **`ModelNumberRecognizer`**: Extracting specific model numbers from labels.
6.  **`DuplicateDetector`**: Comparing images against a reference set to find duplicates.
7.  **`DamageDetector`**: Specific assessment for wear, tear, or damage.

## How to Extend

To add a new implementation for any of these tasks:

1.  Create a new class that implements the desired `Protocol` from `interfaces.py`.
2.  Instantiate your class and pass it to the `ImageAnalysisPipeline`.

### Example

```python
from analysis.images.interfaces import ImageOCR
from analysis.images.pipeline import ImageAnalysisPipeline

class MyAwesomeOCR:
    def extract_text(self, image_url: str) -> str:
        return "Extracted text from MyAwesomeOCR"

pipeline = ImageAnalysisPipeline(ocr=MyAwesomeOCR())
result = pipeline.process_image("http://example.com/image.jpg")
print(result.ocr_text)
```

## AIPlugin Integration

The `ImageAnalysisPipeline` implements the `run` method, making it compatible with the `AIPlugin` interface defined in `analysis/ai_interfaces.py`. It can be registered and run as part of the standard analysis flow.
