from PySide6.QtCore import QObject, Signal

class GeometrySignals(QObject):
    object_added = Signal(dict)
    object_updated = Signal(dict)
    object_removed = Signal(str)
    selection_changed = Signal(str)

class ConsoleSignals(QObject):
    output_received = Signal(str)
    error_received = Signal(str)
    prompt_ready = Signal()

class AlgorithmSignals(QObject):
    step_ready = Signal(dict)
    animation_finished = Signal()
    progress_updated = Signal(int)

class AISignals(QObject):
    prediction_ready = Signal(dict)
    training_progress = Signal(int)
    training_finished = Signal(dict)
    error_occurred = Signal(str)
