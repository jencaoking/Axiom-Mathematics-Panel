from PySide6.QtCore import QObject, Signal

class GeometrySignals(QObject):
    def __init__(self):
        super().__init__()
    
    object_added = Signal(dict)
    object_updated = Signal(dict)
    object_removed = Signal(str)
    selection_changed = Signal(str)

class ConsoleSignals(QObject):
    def __init__(self):
        super().__init__()
    
    output_received = Signal(str)
    error_received = Signal(str)
    prompt_ready = Signal()

class AlgorithmSignals(QObject):
    def __init__(self):
        super().__init__()
    
    step_ready = Signal(dict)
    animation_finished = Signal()
    progress_updated = Signal(int)

class AISignals(QObject):
    def __init__(self):
        super().__init__()
    
    prediction_ready = Signal(dict)
    training_progress = Signal(int)
    training_finished = Signal(dict)
    error_occurred = Signal(str)
