from analysis.ai_interfaces import (
    AnalysisArtifacts,
    AIPlugin,
    ListingContext,
    PluginRegistry,
    run_plugins,
)


class EchoPlugin(AIPlugin):
    name = "echo"

    def run(
        self, context: ListingContext, artifacts: AnalysisArtifacts
    ) -> AnalysisArtifacts:
        artifacts.llm_summary = f"processed {context.title or 'listing'}"
        return artifacts


def test_plugin_registry_can_register_and_resolve_plugins() -> None:
    registry = PluginRegistry()
    registry.register(EchoPlugin())

    plugin = registry.get("echo")
    assert plugin is not None
    assert plugin.name == "echo"


def test_run_plugins_updates_artifacts_without_mutating_context() -> None:
    context = ListingContext(title="Vintage lamp")
    artifacts = AnalysisArtifacts()

    updated = run_plugins(context, [EchoPlugin()], artifacts)

    assert updated.llm_summary == "processed Vintage lamp"
    assert context.title == "Vintage lamp"
