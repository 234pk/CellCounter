import cv2
import numpy as np
from typing import List, Optional, Tuple
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, Signal, QPointF, QRect
from PySide6.QtGui import (
    QPixmap, QColor, QPainter, QPen, QBrush, QFont, 
    QPolygonF, QLinearGradient, QImage
)
from PySide6.QtWidgets import QLabel
from gui.styles import VIEWER_STYLE
from core.utils import cv2_imread

class PolygonViewer(QLabel):
    """Polygon ROI Viewer with mode-based interaction"""

    polygon_changed = Signal()
    
    MODE_ROI = "roi"
    MODE_MANUAL = "manual"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(VIEWER_STYLE)
        self.setMinimumSize(400, 300)
        self.setText("<div style='color: #666; font-size: 16px;'>📷 Click 'Import' to start<br><br>💡 Shift+Left: Add ROI points | Right: Close ROI</div>")

        self.original_pixmap: Optional[QPixmap] = None
        self.image_np = None
        self.polygon_points: List[QPointF] = []
        self.preview_cells = []
        self.current_mode = self.MODE_ROI
        self._selected_vertex = -1
        self._selected_cell = -1
        
        # Zoom and Pan parameters
        self.zoom_factor = 1.0
        self.offset = QPointF(0, 0)
        self.last_mouse_pos = QPointF(0, 0)
        self.is_panning = False
        
        self.setAcceptDrops(True)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def setFocusPolicy(self, policy):
        super().setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def keyPressEvent(self, event):
        """Handle arrow keys for panning and +/- for zooming"""
        pan_step = 20 / self.zoom_factor
        if event.key() == Qt.Key.Key_Left:
            self.offset += QPointF(pan_step, 0)
        elif event.key() == Qt.Key.Key_Right:
            self.offset += QPointF(-pan_step, 0)
        elif event.key() == Qt.Key.Key_Up:
            self.offset += QPointF(0, pan_step)
        elif event.key() == Qt.Key.Key_Down:
            self.offset += QPointF(0, -pan_step)
        elif event.key() == Qt.Key.Key_Plus or event.key() == Qt.Key.Key_Equal:
            self._zoom_at_center(1.25)
        elif event.key() == Qt.Key.Key_Minus:
            self._zoom_at_center(0.8)
        else:
            super().keyPressEvent(event)
        self.update()

    def _zoom_at_center(self, zoom_step):
        new_zoom = self.zoom_factor * zoom_step
        if 0.1 <= new_zoom <= 20.0:
            center = QPointF(self.width() / 2, self.height() / 2)
            img_pos = self.get_scaled_point(center)
            self.zoom_factor = new_zoom
            self._update_display()
            new_screen_pos = self.get_screen_point(img_pos)
            self.offset += (center - new_screen_pos)

    def wheelEvent(self, event):
        """Handle mouse wheel for zooming"""
        if not self.original_pixmap:
            return
            
        # Calculate zoom delta
        delta = event.angleDelta().y()
        zoom_step = 1.25 if delta > 0 else 0.8
        
        # Limit zoom range
        new_zoom = self.zoom_factor * zoom_step
        if new_zoom < 0.1 or new_zoom > 20.0:
            return
            
        # Zoom relative to mouse position
        mouse_pos = event.position()
        
        # 1. Get image point under mouse before zoom
        img_pos = self.get_scaled_point(mouse_pos)
        
        # 2. Update zoom
        self.zoom_factor = new_zoom
        self._update_display()
        
        # 3. Get where that image point is on screen after zoom (with current offset)
        new_screen_pos = self.get_screen_point(img_pos)
        
        # 4. Adjust offset to keep image point under mouse
        # Offset = ScreenTarget - ScreenCurrent
        self.offset += (mouse_pos - new_screen_pos)
        
        self.update()

    def set_mode(self, mode: str):
        self.current_mode = mode
        if mode == self.MODE_ROI:
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.setCursor(Qt.CursorShape.PointingHandCursor)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    path = url.toLocalFile()
                    if path.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff', '.tif')):
                        if self.load_image(path):
                            self.window()._on_image_dropped(self, path)
                            break
            event.acceptProposedAction()

    def load_image(self, path: str) -> bool:
        try:
            self.image_np = cv2_imread(path)
            if self.image_np is None:
                return False
            self.original_pixmap = self.cv2_to_pixmap(self.image_np)
            self._update_display()
            self.polygon_points = []
            self.preview_cells = []
            self.setText("")
            return True
        except Exception as e:
            print(f"Error loading image: {e}")
            return False

    def cv2_to_pixmap(self, image) -> QPixmap:
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        return QPixmap.fromImage(qt_image)

    def _update_display(self):
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update()

    def get_scaled_point(self, pos) -> QPointF:
        if not self.original_pixmap:
            return pos
        display_rect = self.get_image_display_rect()
        
        # Adjust for offset (panning)
        adjusted_pos_x = pos.x() - display_rect.x() - self.offset.x()
        adjusted_pos_y = pos.y() - display_rect.y() - self.offset.y()
        
        # Scale factor accounts for both container fit and zoom_factor
        scale_x = self.original_pixmap.width() / display_rect.width()
        scale_y = self.original_pixmap.height() / display_rect.height()
        
        return QPointF(adjusted_pos_x * scale_x, adjusted_pos_y * scale_y)

    def get_screen_point(self, img_point) -> QPointF:
        if not self.original_pixmap:
            return img_point
        display_rect = self.get_image_display_rect()
        
        scale_x = display_rect.width() / self.original_pixmap.width()
        scale_y = display_rect.height() / self.original_pixmap.height()
        
        # Screen point includes base offset + panning offset
        screen_x = img_point.x() * scale_x + display_rect.x() + self.offset.x()
        screen_y = img_point.y() * scale_y + display_rect.y() + self.offset.y()
        
        return QPointF(screen_x, screen_y)

    def get_image_display_rect(self) -> QRect:
        if not self.original_pixmap:
            return QRect()
        label_size = self.size()
        
        # Calculate size that fits label while keeping aspect ratio
        scaled_size = self.original_pixmap.size()
        scaled_size.scale(label_size * self.zoom_factor, Qt.AspectRatioMode.KeepAspectRatio)
        
        # Center position relative to label
        x_offset = (label_size.width() - scaled_size.width()) / 2
        y_offset = (label_size.height() - scaled_size.height()) / 2
        
        return QRect(int(x_offset), int(y_offset), scaled_size.width(), scaled_size.height())

    def mousePressEvent(self, event):
        if not self.original_pixmap:
            return
            
        if event.button() == Qt.MouseButton.MiddleButton:
            self.is_panning = True
            self.last_mouse_pos = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            return

        img_pos = self.get_scaled_point(event.pos())
        
        if self.current_mode == self.MODE_MANUAL:
            if event.button() == Qt.MouseButton.LeftButton:
                # Add cell in manual mode
                self.preview_cells.append((img_pos.x(), img_pos.y(), 10.0))
                self.polygon_changed.emit()
                self.update()
            elif event.button() == Qt.MouseButton.RightButton:
                # Remove nearest cell in manual mode
                idx_to_remove = -1
                min_dist = 30
                for i, (cx, cy, _) in enumerate(self.preview_cells):
                    dist = ((cx - img_pos.x())**2 + (cy - img_pos.y())**2)**0.5
                    if dist < min_dist:
                        min_dist = dist
                        idx_to_remove = i
                if idx_to_remove >= 0:
                    self.preview_cells.pop(idx_to_remove)
                    self.polygon_changed.emit()
                    self.update()
            return

        # ROI MODE logic
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if clicking on existing vertex to move it
            for i, p in enumerate(self.polygon_points):
                dist = ((p.x() - img_pos.x())**2 + (p.y() - img_pos.y())**2)**0.5
                if dist < 15:
                    self._selected_vertex = i
                    self._selected_cell = -1
                    self.update()
                    return
            
            # Add new ROI point
            self.polygon_points.append(img_pos)
            self._selected_vertex = -1
            self.polygon_changed.emit()
            self.update()
            
        elif event.button() == Qt.MouseButton.RightButton:
            # Delete selected ROI point
            if self._selected_vertex >= 0:
                self.polygon_points.pop(self._selected_vertex)
                self._selected_vertex = -1
                self.polygon_changed.emit()
                self.update()
            elif self.polygon_points:
                self.polygon_points.pop() # Remove last point
                self.polygon_changed.emit()
                self.update()

    def mouseMoveEvent(self, event):
        if not self.original_pixmap:
            return
            
        # Handle Panning
        if self.is_panning:
            delta = event.position() - self.last_mouse_pos
            self.offset += delta
            self.last_mouse_pos = event.position()
            self.update()
            return

        img_pos = self.get_scaled_point(event.pos())
        if self._selected_vertex >= 0 and event.buttons() & Qt.MouseButton.LeftButton:
            self.polygon_points[self._selected_vertex] = img_pos
            self.polygon_changed.emit()
            self.update()
        elif self._selected_cell >= 0 and event.buttons() & Qt.MouseButton.LeftButton:
            cx, cy, size = self.preview_cells[self._selected_cell]
            self.preview_cells[self._selected_cell] = (img_pos.x(), img_pos.y(), size)
            self.polygon_changed.emit()
            self.update()
        else:
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self.is_panning = False
            self.set_mode(self.current_mode) # Restore cursor
            return
            
        self._selected_vertex = -1
        self._selected_cell = -1

    def paintEvent(self, event):
        if not self.original_pixmap:
            super().paintEvent(event)
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # 1. Draw the scaled and panned image
        display_rect = self.get_image_display_rect()
        # Use QRectF for smoother sub-pixel panning/zooming
        target_rect = QtCore.QRectF(display_rect).translated(self.offset)
        painter.drawPixmap(target_rect, self.original_pixmap, QtCore.QRectF(self.original_pixmap.rect()))
        
        # 2. Draw overlays
        scale_factor = display_rect.width() / self.original_pixmap.width()
        
        # Draw ROI Points and Lines (including preview for < 3 points)
        if self.polygon_points:
            screen_points = [self.get_screen_point(p) for p in self.polygon_points]
            
            # Draw lines between existing points
            if len(screen_points) >= 2:
                painter.setPen(QPen(QColor(0, 212, 255), 3))
                for i in range(len(screen_points) - 1):
                    painter.drawLine(screen_points[i], screen_points[i+1])
                
                # Close the polygon if 3+ points
                if len(screen_points) >= 3:
                    painter.drawLine(screen_points[-1], screen_points[0])
                    
                    # Draw filled area
                    gradient = QLinearGradient(screen_points[0], screen_points[-1])
                    gradient.setColorAt(0, QColor(0, 212, 255, 60))
                    gradient.setColorAt(1, QColor(0, 120, 215, 60))
                    painter.setBrush(QBrush(gradient))
                    painter.drawPolygon(QPolygonF(screen_points))

            # Draw vertices
            for i, point in enumerate(screen_points):
                painter.setBrush(QBrush(QColor(0, 255, 136)))
                painter.setPen(QPen(QColor(255, 255, 255), 2))
                painter.drawEllipse(point, 6, 6)
                painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
                painter.setPen(QPen(QColor(255, 255, 255)))
                painter.drawText(int(point.x() + 12), int(point.y() + 4), str(i + 1))
        if self.preview_cells:
            for j, (img_x, img_y, original_size) in enumerate(self.preview_cells):
                screen_point = self.get_screen_point(QPointF(img_x, img_y))
                scaled_radius = (original_size * scale_factor) / 2.0
                painter.setPen(QPen(QColor(255, 50, 50, 200), 1, Qt.PenStyle.DotLine))
                painter.setBrush(QBrush(QColor(255, 50, 50, 40)))
                painter.drawEllipse(screen_point, scaled_radius, scaled_radius)
                painter.setFont(QFont("Arial", 8))
                painter.setPen(QPen(QColor(255, 255, 0, 180)))
                painter.drawText(int(screen_point.x() + scaled_radius + 1),
                               int(screen_point.y() - scaled_radius - 1), str(j + 1))

    def set_preview_cells(self, cells: List[Tuple]):
        if self.original_pixmap:
            self.preview_cells = list(cells)
            self.update()

    def clear_polygon(self):
        self.polygon_points = []
        self.preview_cells = []
        self._selected_vertex = -1
        self._selected_cell = -1
        self.update()
        self.polygon_changed.emit()
    
    def clear_cells(self):
        self.preview_cells = []
        self._selected_cell = -1
        self.update()
        self.polygon_changed.emit()

    def reset_view(self):
        """Reset zoom and pan to default"""
        self.zoom_factor = 1.0
        self.offset = QPointF(0, 0)
        self.update()

    def get_polygon_mask(self, img_shape=None) -> Optional[np.ndarray]:
        if not self.polygon_points or len(self.polygon_points) < 3:
            return None
            
        if img_shape is None:
            if not self.original_pixmap: return None
            h, w = self.original_pixmap.height(), self.original_pixmap.width()
        else:
            h, w = img_shape[:2]
            
        mask = np.zeros((h, w), dtype=np.uint8)
        pts = np.array([[p.x(), p.y()] for p in self.polygon_points], dtype=np.int32)
        cv2.fillPoly(mask, [pts], 255)
        return mask

    def get_polygon_area(self) -> float:
        if len(self.polygon_points) < 3:
            return 0
        points = np.array([[int(p.x()), int(p.y())] for p in self.polygon_points], np.float64)
        n = len(points)
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += points[i][0] * points[j][1]
            area -= points[j][0] * points[i][1]
        return abs(area) / 2.0
