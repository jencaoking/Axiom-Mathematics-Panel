from PySide6.QtCore import QObject, Signal

class GeometrySignals(QObject):
    def __init__(self):
        super().__init__()
    
    object_added = Signal(object)
    object_updated = Signal(object)
    object_removed = Signal(str)
    selection_changed = Signal(str)
    equation_changed = Signal(str, str)
    signals_blocked_changed = Signal(bool)

class ConsoleSignals(QObject):
    def __init__(self):
        super().__init__()
    
    output_received = Signal(str)
    error_received = Signal(str)
    prompt_ready = Signal()

class AlgorithmSignals(QObject):
    def __init__(self):
        super().__init__()
    
    step_ready = Signal(object)
    animation_finished = Signal()
    progress_updated = Signal(int)

class AISignals(QObject):
    def __init__(self):
        super().__init__()
    
    prediction_ready = Signal(object)
    training_progress = Signal(int, float)
    training_finished = Signal(object)
    error_occurred = Signal(str)
