from lightning.app.runners import MultiProcessRuntime
from lightning.app.testing import LightningTestApp

from lightning_hpo.app.main import ResearchStudio
from lightning_hpo.controllers import controller
from tests.helpers import MockDatabaseClient


class MainLightningTestApp(LightningTestApp):
    def on_before_run_once(self):
        res = super().on_before_run_once()
        if self.root.ready:
            return True
        return res


def test_main(monkeypatch):
    monkeypatch.setattr(controller, "DatabaseClient", MockDatabaseClient)

    flow = ResearchStudio()
    app = MainLightningTestApp(flow)
    MultiProcessRuntime(app).dispatch()
