from __future__ import annotations

from dataclasses import dataclass

from analysis.ai_interfaces import AnalysisArtifacts, ListingContext
from analysis.images.interfaces import (
    BrandRecognizer,
    DamageDetector,
    DuplicateDetector,
    ImageClassifier,
    ImageOCR,
    ModelNumberRecognizer,
    ObjectDetector,
)
from analysis.images.types import ImageAnalysisResult


@dataclass
class ImageAnalysisPipeline:
    """Orchestrates multiple image analysis tasks."""

    ocr: ImageOCR | None = None
    object_detector: ObjectDetector | None = None
    classifier: ImageClassifier | None = None
    brand_recognizer: BrandRecognizer | None = None
    model_recognizer: ModelNumberRecognizer | None = None
    duplicate_detector: DuplicateDetector | None = None
    damage_detector: DamageDetector | None = None

    name: str = "image_pipeline"

    def process_image(
        self, image_url: str, reference_urls: list[str] | None = None
    ) -> ImageAnalysisResult:
        """Run all configured analysis steps on a single image."""
        result = ImageAnalysisResult(image_url=image_url)

        if self.ocr:
            result.ocr_text = self.ocr.extract_text(image_url)

        if self.object_detector:
            result.objects = self.object_detector.detect_objects(image_url)

        if self.classifier:
            result.labels = self.classifier.classify(image_url)

        if self.brand_recognizer:
            result.brands = self.brand_recognizer.identify_brands(image_url)

        if self.model_recognizer:
            result.model_numbers = self.model_recognizer.identify_models(image_url)

        if self.duplicate_detector:
            result.is_duplicate = self.duplicate_detector.check_duplicate(
                image_url, reference_urls or []
            )

        if self.damage_detector:
            is_damaged, details = self.damage_detector.detect_damage(image_url)
            result.damage_detected = is_damaged
            result.damage_details = details

        return result

    def run(
        self, context: ListingContext, artifacts: AnalysisArtifacts
    ) -> AnalysisArtifacts:
        """AIPlugin compatible entry point."""
        # For now, we assume the context might have image URLs in raw_data or similar
        # This is a bridge between the core analysis flow and this specialized pipeline
        image_urls = context.raw_data.get("image_urls", [])
        if not image_urls and context.url:
            # Fallback if no images are found but we have a URL (might be useful for some collectors)
            pass

        all_results = []
        for url in image_urls:
            res = self.process_image(url)
            all_results.append(res)

        # Update artifacts
        if all_results:
            # Aggregate data into artifacts
            artifacts.ocr_text = " ".join(
                [r.ocr_text for r in all_results if r.ocr_text]
            )

            labels = set(artifacts.image_labels)
            objects = set(artifacts.detected_objects)

            for r in all_results:
                labels.update([label.label for label in r.labels])
                objects.update([obj.label for obj in r.objects])

            artifacts.image_labels = list(labels)
            artifacts.detected_objects = list(objects)

            # We could add more fields to AnalysisArtifacts if needed,
            # but for now we use what's available.
            artifacts.raw_data["image_analysis"] = [r.__dict__ for r in all_results]

        return artifacts
