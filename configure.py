import json
import asyncio
import httpx
from pathlib import Path
from typing import List, Optional

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import (
    Header, Footer, Button, Input, Label, RadioSet, RadioButton, 
    Select, Static, ContentSwitcher
)
from textual.reactive import reactive
from textual.validation import Function

from utils import AppConfig, ProviderType, ServiceName

CONFIG_FILE = Path("config.json")

class ConfiguratorApp(App):
    CSS = """
    Container {
        padding: 1 2;
    }
    .section {
        margin-bottom: 1;
        padding: 1;
        border: solid green;
        height: auto;
        min-height: 5;
    }
    .hidden {
        display: none;
    }
    Label {
        margin-top: 1;
        text-style: bold;
        color: cyan;
    }
    RadioButton {
        width: 100%;
    }
    Button {
        margin-top: 1;
        width: 100%;
    }
    RadioSet {
        height: auto;
        min-height: 3;
    }
    #main-container {
        overflow-y: scroll;
    }
    #model-row {
        height: 5;
        margin-top: 1;
    }
    #model-select {
        width: 70%;
    }
    #manual-btn {
        width: 30%;
        margin-top: 0;
    }
    #save-btn {
        background: green;
        color: white;
        margin-top: 2;
    }
    """

    TITLE = "LLM Configurator"
    SUB_TITLE = "YouTube Transcript Downloader"
    BINDINGS = [("q", "quit", "Quit")]

    provider = reactive(ProviderType.LOCAL)
    service = reactive(ServiceName.OLLAMA)
    available_models = reactive([])

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Vertical(
                Label("1. Choose Provider"),
                RadioSet(
                    RadioButton("Local (Ollama, LM Studio)", value=True, id="local-radio"),
                    RadioButton("Cloud (Gemini, OpenAI, Anthropic)", id="cloud-radio"),
                    id="provider-set"
                ),
                classes="section"
            ),
            
            Vertical(
                Label("2. Choose Service"),
                ContentSwitcher(
                    RadioSet(
                        RadioButton("Ollama", value=True, id="ollama-radio"),
                        RadioButton("LM Studio", id="lm-studio-radio"),
                        id="local-service-set"
                    ),
                    RadioSet(
                        RadioButton("Gemini", value=True, id="gemini-radio"),
                        RadioButton("OpenAI", id="openai-radio"),
                        RadioButton("Anthropic", id="anthropic-radio"),
                        id="cloud-service-set"
                    ),
                    id="service-switcher"
                ),
                classes="section"
            ),

            Vertical(
                Label("3. Configure Connection"),
                Label("Service URL", id="url-label"),
                Input(value="http://localhost:11434", id="url-input"),
                
                Label("API Key", id="key-label", classes="hidden"),
                Input(password=True, id="key-input", classes="hidden"),
                
                Label("Model Selection"),
                Horizontal(
                    Select([], prompt="Fetching models...", id="model-select"),
                    Button("Manual Entry", id="manual-btn", variant="primary"),
                    id="model-row"
                ),
                Input(placeholder="Enter model name manually...", id="model-input", classes="hidden"),
                
                Button("Save Configuration", id="save-btn", variant="success"),
                classes="section"
            ),
            id="main-container"
        )
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#service-switcher").current = "local-service-set"
        asyncio.create_task(self.update_models())

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        if event.radio_set.id == "provider-set":
            self.provider = ProviderType.LOCAL if event.pressed.id == "local-radio" else ProviderType.CLOUD
            # Use .value to get "local" or "cloud" instead of "ProviderType.LOCAL"
            self.query_one("#service-switcher").current = f"{self.provider.value}-service-set"
            
            # Toggle visibility of URL/Key inputs
            is_local = self.provider == ProviderType.LOCAL
            self.query_one("#url-label").set_class(not is_local, "hidden")
            self.query_one("#url-input").set_class(not is_local, "hidden")
            self.query_one("#key-label").set_class(is_local, "hidden")
            self.query_one("#key-input").set_class(is_local, "hidden")
            
            # Update default URL based on service
            if is_local:
                self.update_default_url()
            else:
                self.query_one("#model-select").options = [
                    ("gemini-1.5-pro", "gemini-1.5-pro"),
                    ("gemini-1.5-flash", "gemini-1.5-flash"),
                    ("gpt-4o", "gpt-4o"),
                    ("claude-3-5-sonnet-20240620", "claude-3-5-sonnet-20240620")
                ]

        elif event.radio_set.id in ["local-service-set", "cloud-service-set"]:
            mapping = {
                "ollama-radio": ServiceName.OLLAMA,
                "lm-studio-radio": ServiceName.LM_STUDIO,
                "gemini-radio": ServiceName.GEMINI,
                "openai-radio": ServiceName.OPENAI,
                "anthropic-radio": ServiceName.ANTHROPIC
            }
            self.service = mapping[event.pressed.id]
            if self.provider == ProviderType.LOCAL:
                self.update_default_url()
            
            asyncio.create_task(self.update_models())

    def update_default_url(self) -> None:
        url_input = self.query_one("#url-input")
        if self.service == ServiceName.OLLAMA:
            url_input.value = "http://localhost:11434"
        elif self.service == ServiceName.LM_STUDIO:
            url_input.value = "http://localhost:1234"

    async def update_models(self) -> None:
        select = self.query_one("#model-select")
        
        if self.provider == ProviderType.CLOUD:
            select.disabled = False
            return

        url = self.query_one("#url-input").value
        # Basic URL validation before trying
        if not url.startswith("http"):
            return

        select.prompt = "Discovering..."
        
        models = []
        try:
            async with httpx.AsyncClient() as client:
                if self.service == ServiceName.OLLAMA:
                    resp = await client.get(f"{url}/api/tags", timeout=3)
                    if resp.status_code == 200:
                        data = resp.json()
                        models = [(m["name"], m["name"]) for m in data.get("models", [])]
                elif self.service == ServiceName.LM_STUDIO:
                    resp = await client.get(f"{url}/v1/models", timeout=3)
                    if resp.status_code == 200:
                        data = resp.json()
                        models = [(m["id"], m["id"]) for m in data.get("data", [])]
        except Exception as e:
            # Only notify on explicit discovery or long enough URL
            if len(url) > 15:
                self.notify(f"Connection failed: {e}", severity="warning")
            if self.service == ServiceName.OLLAMA:
                self.notify("💡 Tip: Ensure 'ollama serve' is running and you have pulled models.", severity="information", timeout=6)

        if models:
            select.set_options(models)
            select.prompt = "Select a model"
            select.disabled = False
            select.refresh()
            self.notify(f"Found {len(models)} models from {self.service}", severity="information")
        else:
            select.set_options([])
            if self.service == ServiceName.OLLAMA:
                select.prompt = "No models found (Is Ollama running?)"
            else:
                select.prompt = "No models found"
            select.disabled = True
            select.refresh()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "url-input":
            # Debounce: stop previous timer and start a new one
            if hasattr(self, "_discovery_timer"):
                self._discovery_timer.stop()
            self._discovery_timer = self.set_timer(1.0, self.update_models)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "manual-btn":
            input_widget = self.query_one("#model-input")
            input_widget.toggle_class("hidden")
            select_widget = self.query_one("#model-select")
            select_widget.toggle_class("hidden")
            
            if not input_widget.has_class("hidden"):
                input_widget.focus()
                event.button.label = "Use List"
            else:
                event.button.label = "Manual Entry"
        
        elif event.button.id == "save-btn":
            self.save_config()

    def save_config(self) -> None:
        from textual.markup import escape
        
        model_val = self.query_one("#model-input").value
        if self.query_one("#model-input").has_class("hidden"):
            selection = self.query_one("#model-select").value
            # Handle both Select.BLANK and Select.NULL (no selection)
            if selection in (Select.BLANK, Select.NULL) or selection is None:
                self.notify("Please select a model or enter one manually", severity="error")
                return
            model_val = str(selection)

        try:
            config = AppConfig(
                provider=self.provider,
                service=self.service,
                url=self.query_one("#url-input").value if self.provider == ProviderType.LOCAL else None,
                model=model_val,
                api_key=self.query_one("#key-input").value if self.provider == ProviderType.CLOUD else None
            )
            
            with open(CONFIG_FILE, "w") as f:
                f.write(config.model_dump_json(indent=2))
            
            self.notify(f"Configuration saved to {escape(str(CONFIG_FILE))}")
            self.exit()
        except Exception as e:
            self.notify(f"Validation Error: {escape(str(e))}", severity="error")

def main():
    app = ConfiguratorApp()
    app.run()

if __name__ == "__main__":
    main()
