from __future__ import annotations

import string
from typing import Any, Dict


class PromptManager:
    """Manages AI prompt templates and formatting."""

    TEMPLATES = {
        "title_normalization": (
            "Normalize the following marketplace listing title for better searchability. "
            "Remove unnecessary emojis, symbols, and clickbait words. "
            "Keep important details like brand, model, and condition if present.\n\n"
            "Original Title: ${title}\n"
            "Normalized Title:"
        ),
        "description_cleanup": (
            "Clean up and summarize the following listing description. "
            "Extract key specifications and remove redundant text.\n\n"
            "Description: ${description}\n\n"
            "Cleaned Description:"
        ),
        "seller_motivation": (
            "Analyze the following listing and seller description to determine the seller's motivation. "
            "Are they in a hurry? Is it a moving sale? Are they firm on price? "
            "Return a brief assessment.\n\n"
            "Title: ${title}\n"
            "Description: ${description}\n\n"
            "Assessment:"
        ),
        "category_classification": (
            "Classify the following listing into one of these categories: ${categories}.\n\n"
            "Title: ${title}\n"
            "Description: ${description}\n\n"
            "Category:"
        ),
        "repair_estimation": (
            "Based on the description and title, estimate the difficulty and potential cost of repair "
            "if any damage is mentioned. If no damage is mentioned, state 'No repair needed'.\n\n"
            "Title: ${title}\n"
            "Description: ${description}\n\n"
            "Repair Estimate:"
        ),
        "risk_analysis": (
            "Analyze the following listing for potential risks (scams, hidden damage, stolen goods). "
            "Provide a risk score from 0-100 and a brief explanation.\n\n"
            "Title: ${title}\n"
            "Description: ${description}\n"
            "Price: ${price}\n\n"
            "Risk Analysis:"
        ),
        "recommendation_generation": (
            "Generate a brief recommendation for a buyer interested in this listing. "
            "Highlight the pros and cons based on the available data.\n\n"
            "Title: ${title}\n"
            "Description: ${description}\n"
            "FlipScore: ${flipscore}\n\n"
            "Recommendation:"
        ),
    }

    def get_prompt(self, template_name: str, **kwargs: Any) -> str:
        """Get a formatted prompt for a given template name."""
        template_str = self.TEMPLATES.get(template_name)
        if not template_str:
            raise ValueError(f"Template '{template_name}' not found.")
        
        template = string.Template(template_str)
        return template.safe_substitute(**kwargs)

    def add_template(self, name: str, template: str) -> None:
        """Add a new template to the manager."""
        self.TEMPLATES[name] = template
