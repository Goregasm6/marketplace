from unittest.mock import MagicMock

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
from analysis.images.pipeline import ImageAnalysisPipeline
from analysis.images.types import ImageDetection


def test_pipeline_orchestration():
    # Setup mocks
    mock_ocr = MagicMock(spec=ImageOCR)
    mock_ocr.extract_text.return_value = "Test OCR Text"

    mock_detector = MagicMock(spec=ObjectDetector)
    mock_detector.detect_objects.return_value = [
        ImageDetection(label="laptop", confidence=0.9)
    ]

    mock_classifier = MagicMock(spec=ImageClassifier)
    mock_classifier.classify.return_value = [
        ImageDetection(label="electronics", confidence=0.95)
    ]

    mock_brand = MagicMock(spec=BrandRecognizer)
    mock_brand.identify_brands.return_value = ["Apple"]

    mock_model = MagicMock(spec=ModelNumberRecognizer)
    mock_model.identify_models.return_value = ["MacBookPro16,1"]

    mock_duplicate = MagicMock(spec=DuplicateDetector)
    mock_duplicate.check_duplicate.return_value = True

    mock_damage = MagicMock(spec=DamageDetector)
    mock_damage.detect_damage.return_value = (True, "Screen crack")

    # Initialize pipeline
    pipeline = ImageAnalysisPipeline(
        ocr=mock_ocr,
        object_detector=mock_detector,
        classifier=mock_classifier,
        brand_recognizer=mock_brand,
        model_recognizer=mock_model,
        duplicate_detector=mock_duplicate,
        damage_detector=mock_damage,
    )

    # Process image
    result = pipeline.process_image("http://example.com/test.jpg")

    # Assertions
    assert result.image_url == "http://example.com/test.jpg"
    assert result.ocr_text == "Test OCR Text"
    assert len(result.objects) == 1
    assert result.objects[0].label == "laptop"
    assert result.labels[0].label == "electronics"
    assert result.brands == ["Apple"]
    assert result.model_numbers == ["MacBookPro16,1"]
    assert result.is_duplicate is True
    assert result.damage_detected is True
    assert result.damage_details == "Screen crack"


def test_pipeline_as_ai_plugin():
    mock_ocr = MagicMock(spec=ImageOCR)
    mock_ocr.extract_text.return_value = "Plugin OCR"

    pipeline = ImageAnalysisPipeline(ocr=mock_ocr)

    context = ListingContext(
        raw_data={
            "image_urls": ["http://example.com/1.jpg", "http://example.com/2.jpg"]
        }
    )
    artifacts = AnalysisArtifacts()

    updated_artifacts = pipeline.run(context, artifacts)

    assert "Plugin OCR Plugin OCR" in updated_artifacts.ocr_text
    assert "image_analysis" in updated_artifacts.raw_data
    assert len(updated_artifacts.raw_data["image_analysis"]) == 2
