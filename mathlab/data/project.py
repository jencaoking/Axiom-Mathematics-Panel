import json
import os
from datetime import datetime

class ProjectManager:
    def __init__(self):
        self.current_project = None
        self.objects = {}
        self.console_history = []
        self.settings = {
            'created': datetime.now().isoformat(),
            'modified': datetime.now().isoformat(),
            'version': '1.0'
        }
    
    def new_project(self):
        self.current_project = None
        self.objects = {}
        self.console_history = []
        self.settings = {
            'created': datetime.now().isoformat(),
            'modified': datetime.now().isoformat(),
            'version': '1.0'
        }
    
    def open_project(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.current_project = file_path
            self.objects = data.get('objects', {})
            self.console_history = data.get('console_history', [])
            self.settings = data.get('settings', {})
            
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def save_project(self, file_path=None):
        if file_path is None:
            file_path = self.current_project
        
        if file_path is None:
            return {'success': False, 'error': 'No file path specified'}
        
        try:
            data = {
                'objects': self.objects,
                'console_history': self.console_history,
                'settings': {
                    **self.settings,
                    'modified': datetime.now().isoformat()
                }
            }
            
            tmp_path = file_path + '.tmp'
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            os.replace(tmp_path, file_path)
            
            self.current_project = file_path
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def add_object(self, obj_id, obj_data):
        self.objects[obj_id] = obj_data
        self._update_modified()
    
    def _deep_update(self, target, source):
        for key, value in source.items():
            if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                self._deep_update(target[key], value)
            else:
                target[key] = value

    def update_object(self, obj_id, obj_data):
        if obj_id in self.objects:
            self._deep_update(self.objects[obj_id], obj_data)
            self._update_modified()
    
    def remove_object(self, obj_id):
        if obj_id in self.objects:
            del self.objects[obj_id]
            self._update_modified()
    
    def add_console_entry(self, entry):
        self.console_history.append({
            'timestamp': datetime.now().isoformat(),
            'entry': entry
        })
        if len(self.console_history) > 1000:
            self.console_history = self.console_history[-1000:]
    
    def get_object(self, obj_id):
        return self.objects.get(obj_id)
    
    def get_all_objects(self):
        return list(self.objects.values())
    
    def _update_modified(self):
        self.settings['modified'] = datetime.now().isoformat()
    
    def export_to_png(self, canvas_widget, file_path):
        try:
            pixmap = canvas_widget.grab()
            pixmap.save(file_path)
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def export_to_svg(self, canvas_widget, file_path):
        return {'success': False, 'error': 'SVG export not implemented yet'}
    
    def export_algebra_to_latex(self):
        latex_lines = []
        
        for obj_data in self.objects.values():
            obj_type = obj_data.get('type')
            name = obj_data.get('name', '')
            coords = obj_data.get('coordinates', {})
            
            if obj_type == 'Point':
                x = coords.get('x', 0)
                y = coords.get('y', 0)
                latex_lines.append(rf'\({name} = ({x}, {y})\)')
            elif obj_type == 'Circle':
                cx = coords.get('cx', 0)
                cy = coords.get('cy', 0)
                r = coords.get('r', 1)
                latex_lines.append(rf'\(\text{{Circle}}({name}, ({cx}, {cy}), {r})\)')
        
        return '\n'.join(latex_lines)
