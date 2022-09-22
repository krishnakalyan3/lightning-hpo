import urllib.parse
from typing import List

from lightning.app.storage import Drive

from lightning_hpo.commands.tensorboard.stop import StopTensorboardConfig, TensorboardConfig
from lightning_hpo.components.tensorboard import Tensorboard
from lightning_hpo.controllers.controller import Controller
from lightning_hpo.utilities.enum import Stage


class TensorboardController(Controller):

    model = TensorboardConfig

    def on_reconcile_start(self, configs: List[TensorboardConfig]):
        for config in configs:
            work_name = urllib.parse.quote_plus(config.sweep_id)
            if work_name not in self.r:
                if config.stage in (Stage.STOPPED, Stage.NOT_STARTED) and config.desired_stage == Stage.RUNNING:
                    self.r[work_name] = Tensorboard(
                        drive=Drive(f"lit://{config.sweep_id}"),
                        config=config,
                    )
                    self.r[work_name].stage = Stage.PENDING

    def show_tensorboards(self) -> List[TensorboardConfig]:
        if self.db_url:
            return self.db.get()
        return []

    def run_tensorboard(self, config: TensorboardConfig):
        tensorboards = self.db.get()
        matched_tensorboard = None

        for tensorboard in tensorboards:
            if tensorboard.sweep_id == config.sweep_id:
                matched_tensorboard = config

        if matched_tensorboard:
            matched_tensorboard.stage = Stage.STOPPED
            matched_tensorboard.desired_stage = Stage.RUNNING
            self.db.put(matched_tensorboard)
            return f"Re-Launched a Tensorboard `{config.sweep_id}`."

        self.db.post(config)
        return f"Launched a Tensorboard `{config.sweep_id}`."

    def stop_tensorboard(self, config: StopTensorboardConfig):
        work_name = urllib.parse.quote_plus(config.sweep_id)
        if work_name in self.r:
            self.r[work_name].stop()
            self.r[work_name]._url = ""
            self.r[work_name].stage = Stage.STOPPED
            self.r[work_name].desired_stage = Stage.STOPPED
            self.db.put(self.r[work_name].collect_model())
            del self.r[work_name]
            return f"Tensorboard `{config.sweep_id}` was stopped."
        return f"Tensorboard `{config.sweep_id}` doesn't exist."

    def configure_commands(self):
        return [
            {"run tensorboard": self.run_tensorboard},
            {"show tensorboards": self.show_tensorboards},
            {"stop tensorboard": self.stop_tensorboard},
        ]
