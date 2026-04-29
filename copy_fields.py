import os
from qgis.PyQt.QtWidgets import (QAction, QDialog, QVBoxLayout, QHBoxLayout, 
                                 QLabel, QComboBox, QDialogButtonBox, 
                                 QListWidget, QListWidgetItem, QPushButton)
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import Qt
from qgis.core import QgsProject, Qgis

class CopyFieldsDialog(QDialog):
    def __init__(self, parent=None):
        super(CopyFieldsDialog, self).__init__(parent)
        self.setWindowTitle('Copy Fields to Layer')
        self.resize(350, 400)
        
        layout = QVBoxLayout(self)
        
        # Input Layer Dropdown
        layout.addWidget(QLabel('Input Layer (Has the fields you want):'))
        self.input_cb = QComboBox()
        layout.addWidget(self.input_cb)
        
        # Target Layer Dropdown
        layout.addWidget(QLabel('Target Layer (Where fields will be added):'))
        self.target_cb = QComboBox()
        layout.addWidget(self.target_cb)
        
        # Connect dropdowns to the field updater
        self.input_cb.currentIndexChanged.connect(self.update_fields)
        self.target_cb.currentIndexChanged.connect(self.update_fields)
        
        # Field List (Checklist)
        layout.addWidget(QLabel('Select fields to copy:'))
        self.field_list = QListWidget()
        layout.addWidget(self.field_list)
        
        # Select/Deselect All Buttons
        btn_layout = QHBoxLayout()
        self.btn_select_all = QPushButton("Select All")
        self.btn_deselect_all = QPushButton("Deselect All")
        btn_layout.addWidget(self.btn_select_all)
        btn_layout.addWidget(self.btn_deselect_all)
        layout.addLayout(btn_layout)
        
        self.btn_select_all.clicked.connect(self.select_all)
        self.btn_deselect_all.clicked.connect(self.deselect_all)
        
        # Populate dropdowns with current map layers
        self.populate_layers()
        self.update_fields() # Initial populate of the checklist
        
        # OK and Cancel Buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def populate_layers(self):
        layers = QgsProject.instance().mapLayers().values()
        for layer in layers:
            self.input_cb.addItem(layer.name(), layer.id())
            self.target_cb.addItem(layer.name(), layer.id())

    def update_fields(self):
        self.field_list.clear()
        input_id = self.input_cb.currentData()
        target_id = self.target_cb.currentData()
        
        if not input_id or not target_id or input_id == target_id:
            return
            
        input_layer = QgsProject.instance().mapLayer(input_id)
        target_layer = QgsProject.instance().mapLayer(target_id)
        
        if not input_layer or not target_layer:
            return
            
        # Get a list of existing field names in the target layer
        target_field_names = [f.name() for f in target_layer.fields()]
        
        # Add missing fields to the checklist
        for field in input_layer.fields():
            if field.name() not in target_field_names:
                item = QListWidgetItem(field.name())
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Checked) # Default to checked
                self.field_list.addItem(item)

    def select_all(self):
        for i in range(self.field_list.count()):
            self.field_list.item(i).setCheckState(Qt.Checked)

    def deselect_all(self):
        for i in range(self.field_list.count()):
            self.field_list.item(i).setCheckState(Qt.Unchecked)

class CopyFieldsPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.plugin_dir = os.path.dirname(__file__)

    def initGui(self):
        icon_path = os.path.join(self.plugin_dir, 'icon.png')
        self.action = QAction(QIcon(icon_path), 'Copy Fields Tool', self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        
        self.iface.addPluginToVectorMenu('Copy Fields Tool', self.action)
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        if self.action:
            self.iface.removePluginVectorMenu('Copy Fields Tool', self.action)
            self.iface.removeToolBarIcon(self.action)

    def run(self):
        dialog = CopyFieldsDialog(self.iface.mainWindow())
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            input_id = dialog.input_cb.currentData()
            target_id = dialog.target_cb.currentData()
            
            if not input_id or not target_id:
                self.iface.messageBar().pushMessage("Error", "Please make sure you have layers loaded.", level=Qgis.Critical)
                return
            
            if input_id == target_id:
                self.iface.messageBar().pushMessage("Error", "Input and Target layers cannot be the same.", level=Qgis.Critical)
                return
                
            input_layer = QgsProject.instance().mapLayer(input_id)
            target_layer = QgsProject.instance().mapLayer(target_id)
            
            if not input_layer or not target_layer:
                return

            # Gather the names of the fields the user actually checked
            selected_field_names = []
            for i in range(dialog.field_list.count()):
                item = dialog.field_list.item(i)
                if item.checkState() == Qt.Checked:
                    selected_field_names.append(item.text())

            if not selected_field_names:
                self.iface.messageBar().pushMessage("Notice", "No fields were selected to copy.", level=Qgis.Info)
                return

            # Retrieve the full field properties for the selected names
            new_fields = []
            for field in input_layer.fields():
                if field.name() in selected_field_names:
                    new_fields.append(field)

            # Apply to the target layer
            if new_fields:
                target_layer.dataProvider().addAttributes(new_fields)
                target_layer.updateFields()
                self.iface.messageBar().pushMessage("Success", f"Successfully added {len(new_fields)} new fields to {target_layer.name()}.", level=Qgis.Success)
