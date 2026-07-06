"""文件操作 Mixin（新建/打开/保存/导出）。

将 MainWindow 中与项目文件 I/O 和导出相关的方法提取到此模块。
"""
import json

from PySide6.QtWidgets import QFileDialog, QMessageBox
from PySide6.QtGui import QPainter as QtPainter
from PySide6.QtSvg import QSvgGenerator

try:
    from ..utils.latex_renderer import export_canvas_to_latex
except ImportError:
    from utils.latex_renderer import export_canvas_to_latex

try:
    from ..utils.i18n_manager import t
except ImportError:
    from utils.i18n_manager import t

try:
    from ..utils.logger import get_logger
except ImportError:
    from utils.logger import get_logger

logger = get_logger(__name__)


class FileIOMixin:
    """MainWindow Mixin：文件操作。"""
    def on_new_project(self) -> None:
        self.central_widget.clear_canvas()
        self.algebra_panel.clear()
        self.properties_panel.clear()
        self.console.clear()
        self._objects_data.clear()
        if hasattr(self, 'geometry_engine'):
            self.geometry_engine.clear()
        self.current_project = None

    def on_open_project(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            t('dialogs.open_project'),
            '',
            'MathLab Files (*.mathlab)',
        )
        if not file_path:
            return
        try:
            import json
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.on_new_project()

            if hasattr(self, 'geometry_engine'):
                if 'name_counter' in data:
                    self.geometry_engine.deserialize_all(data)
                else:
                    legacy_data = {'name_counter': 1, 'objects': data.get('objects', {})}
                    self.geometry_engine.deserialize_all(legacy_data)
                    
                self._objects_data = {obj.id: obj.serialize() for obj in self.geometry_engine.get_all_objects()}
                for obj in self.geometry_engine.get_all_objects():
                    self.algebra_panel.add_object(obj.serialize())
                    self.central_widget.draw_object(obj.id, obj.serialize())
            else:
                for obj_id, obj_data in data.get('objects', {}).items():
                    self._add_object(obj_data)

            self.current_project = file_path
            self.statusBar().showMessage(t('status_bar.opened', file_path))
        except Exception as e:
            QMessageBox.warning(
                self,
                t('dialogs.error'),
                t('dialogs.failed_to_open', str(e)),
            )

    def on_save_project(self) -> None:
        if self.current_project:
            self._save_project(self.current_project)
        else:
            self.on_save_project_as()

    def on_save_project_as(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            t('dialogs.save_project_as'),
            '',
            'MathLab Files (*.mathlab)',
        )
        if file_path:
            if not file_path.endswith('.mathlab'):
                file_path += '.mathlab'
            self._save_project(file_path)

    def _save_project(self, file_path: str) -> None:
        try:
            import json
            if hasattr(self, 'geometry_engine'):
                data = self.geometry_engine.serialize_all()
            else:
                data = {'objects': self._objects_data}
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.current_project = file_path
            self.statusBar().showMessage(t('status_bar.saved', file_path))
        except Exception as e:
            QMessageBox.warning(
                self,
                t('dialogs.error'),
                t('dialogs.failed_to_save', str(e)),
            )

    def on_export_png(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self, t('dialogs.export_png'), '', 'PNG Files (*.png)'
        )
        if not file_path:
            return
        if not file_path.endswith('.png'):
            file_path += '.png'
        try:
            pixmap = self.central_widget.grab()
            pixmap.save(file_path)
            self.statusBar().showMessage(t('status_bar.exported', file_path))
        except Exception as e:
            QMessageBox.warning(self, t('dialogs.error'), t('dialogs.failed_to_export', str(e)))

    def on_export_svg(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self, t('dialogs.export_svg'), '', 'SVG Files (*.svg)'
        )
        if not file_path:
            return
        if not file_path.endswith('.svg'):
            file_path += '.svg'
        try:
            svg_generator = QSvgGenerator()
            svg_generator.setFileName(file_path)

            bounding_rect = self.central_widget.scene().itemsBoundingRect()
            svg_generator.setViewBox(bounding_rect)

            painter = QtPainter(svg_generator)
            painter.setRenderHint(QtPainter.Antialiasing)
            self.central_widget.scene().render(painter)
            painter.end()

            self.statusBar().showMessage(t('status_bar.exported_svg', file_path))
        except Exception as e:
            QMessageBox.warning(self, t('dialogs.error'), t('dialogs.failed_to_export', str(e)))

    def on_export_latex(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self, t('dialogs.export_latex'), '', 'LaTeX Files (*.tex)'
        )
        if not file_path:
            return
        if not file_path.endswith('.tex'):
            file_path += '.tex'
        try:
            latex_content = export_canvas_to_latex(list(self._objects_data.values()))
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(latex_content)
            self.statusBar().showMessage(t('status_bar.exported_latex', file_path))
        except Exception as e:
            QMessageBox.warning(self, t('dialogs.error'), t('dialogs.failed_to_export', str(e)))

