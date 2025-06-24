def create_vanilla_patch(self):
        """Create a patch for selected vanilla item"""
        selected = self.vanilla_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a vanilla item to patch")
            return
        
        item_name = self.vanilla_tree.item(selected[0])['text']
        if item_name not in self.vanilla_db.items:
            return
        
        # Create patch item with same name (will override vanilla)
        patch_name = item_name
        
        # Start with minimal patch data
        vanilla_data = self.vanilla_db.items[item_name].copy()
        for key in list(vanilla_data.keys()):
            if key.startswith('_'):
                del vanilla_data[key]
        
        # Mark as patch for special handling
        patch_data = vanilla_data.copy()
        patch_data['_is_patch'] = True
        patch_data['_original_item'] = item_name
        
        self.current_mod[patch_name] = patch_data
        self.refresh_items_list()
        
        # Select the new patch
        for item_id in self.items_tree.get_children():
            if self.items_tree.item(item_id)['text'] == patch_name:
                self.items_tree.selection_set(item_id)
                self.items_tree.focus(item_id)
                break
        
        self.status_var.set(f"Created patch for: {item_name}")
        messagebox.showinfo("Patch Created", 
                           f"Created patch for {item_name}.\n\n"
                           f"Modify the parameters you want to change.\n"
                           f"The patch will only include changed values in the final script.")
    
    def on_template_selected(self, event):
        """Handle template selection"""
        template_key = self.template_var.get()
        if template_key in self.templates:
            template = self.templates[template_key]
            self.template_desc.config(text=template.description)
            self.status_var.set(f"Selected template: {template.description}")
    
    def create_param_widgets(self, item_data, readonly=False):
        """Create parameter widgets based on item data"""
        # Clear existing widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        self.param_vars.clear()
        self.param_widgets.clear()
        
        # Check if this is a patch
        is_patch = item_data.get('_is_patch', False)
        original_item = item_data.get('_original_item', '')
        
        if is_patch:
            # Add patch info header
            patch_info = ttk.LabelFrame(self.scrollable_frame, text="Patch Information", padding=5)
            patch_info.grid(row=0, column=0, columnspan=3, sticky=tk.W+tk.E, pady=(0, 10))
            
            ttk.Label(patch_info, text=f"Patching: {original_item}", 
                     font=("Arial", 9, "bold")).pack(anchor=tk.W)
            ttk.Label(patch_info, text="Only modified parameters will be included in the final script", 
                     font=("Arial", 8), foreground="gray").pack(anchor=tk.W)
        
        row = 1 if is_patch else 0
        
        for param, value in sorted(item_data.items()):
            if param.startswith('_'):  # Skip internal properties
                continue
            
            # Create label
            label = ttk.Label(self.scrollable_frame, text=f"{param}:", width=20, anchor=tk.W)
            label.grid(row=row, column=0, sticky=tk.W, padx=(0, 10), pady=2)
            
            # Create appropriate widget based on parameter type
            var = self.create_param_var(param, value)
            widget = self.create_param_widget(param, value, var, readonly)
            widget.grid(row=row, column=1, sticky=tk.W, pady=2)
            
            self.param_vars[param] = var
            self.param_widgets[param] = widget
            
            row += 1
        
        if not readonly:
            # Add button to add new parameter
            add_param_frame = ttk.Frame(self.scrollable_frame)
            add_param_frame.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=10)
            
            ttk.Button(add_param_frame, text="Add Parameter", command=self.add_parameter).pack(side=tk.LEFT)
            ttk.Button(add_param_frame, text="Update Preview", command=self.update_preview).pack(side=tk.LEFT, padx=(5, 0))
    
    def create_param_widget(self, param, value, var, readonly=False):
        """Create appropriate widget for parameter"""
        frame = ttk.Frame(self.scrollable_frame)
        
        if isinstance(value, bool):
            widget = ttk.Checkbutton(frame, variable=var, state=tk.DISABLED if readonly else tk.NORMAL)
            widget.pack(side=tk.LEFT)
        elif param in ["DisplayCategory", "SubCategory", "Categories", "BodyLocation", "AttachmentType"]:
            # Use combobox for common categorical parameters
            common_values = self.get_common_values(param)
            widget = ttk.Combobox(frame, textvariable=var, values=common_values, width=30,
                                state=tk.DISABLED if readonly else "readonly")
            widget.pack(side=tk.LEFT)
        else:
            widget = ttk.Entry(frame, textvariable=var, width=30,
                             state=tk.DISABLED if readonly else tk.NORMAL)
            widget.pack(side=tk.LEFT)
        
        if not readonly:
            # Add delete button for each parameter
            delete_btn = ttk.Button(frame, text="×", width=3, 
                                   command=lambda p=param: self.delete_parameter(p))
            delete_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        return frame


class SettingsDialog:
    """Settings configuration dialog"""
    
    def __init__(self, parent, config: ConfigManager, app):
        self.config = config
        self.app = app
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Settings")
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the settings dialog UI"""
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Paths tab
        paths_frame = ttk.Frame(notebook)
        notebook.add(paths_frame, text="Paths")
        self.setup_paths_tab(paths_frame)
        
        # UI tab
        ui_frame = ttk.Frame(notebook)
        notebook.add(ui_frame, text="Interface")
        self.setup_ui_tab(ui_frame)
        
        # Validation tab
        validation_frame = ttk.Frame(notebook)
        notebook.add(validation_frame, text="Validation")
        self.setup_validation_tab(validation_frame)
        
        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="OK", command=self.save_and_close).pack(side=tk.RIGHT)
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.RIGHT, padx=(0, 5))
        ttk.Button(button_frame, text="Apply", command=self.apply_settings).pack(side=tk.RIGHT, padx=(0, 5))
    
    def setup_paths_tab(self, parent):
        """Setup paths configuration"""
        # Vanilla scripts path
        vanilla_frame = ttk.LabelFrame(parent, text="Project Zomboid Installation", padding=10)
        vanilla_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(vanilla_frame, text="Vanilla Scripts Path:").pack(anchor=tk.W)
        
        path_frame = ttk.Frame(vanilla_frame)
        path_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.vanilla_path_var = tk.StringVar(value=self.config.get('Paths', 'vanilla_scripts'))
        ttk.Entry(path_frame, textvariable=self.vanilla_path_var, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(path_frame, text="Browse", command=self.browse_vanilla_path).pack(side=tk.RIGHT, padx=(5, 0))
        
        ttk.Button(vanilla_frame, text="Auto-Detect", command=self.auto_detect_vanilla).pack(anchor=tk.W, pady=(5, 0))
        
        # Status
        current_path = self.config.get_vanilla_scripts_path()
        status_text = f"Current: {current_path}" if current_path else "Not configured"
        ttk.Label(vanilla_frame, text=status_text, foreground="gray").pack(anchor=tk.W, pady=(5, 0))
        
        # Output paths
        output_frame = ttk.LabelFrame(parent, text="Output Directories", padding=10)
        output_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(output_frame, text="Mod Output Directory:").pack(anchor=tk.W)
        
        output_path_frame = ttk.Frame(output_frame)
        output_path_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.output_path_var = tk.StringVar(value=self.config.get('Paths', 'mod_output'))
        ttk.Entry(output_path_frame, textvariable=self.output_path_var, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(output_path_frame, text="Browse", command=self.browse_output_path).pack(side=tk.RIGHT, padx=(5, 0))
    
    def setup_ui_tab(self, parent):
        """Setup UI configuration"""
        # Window settings
        window_frame = ttk.LabelFrame(parent, text="Window Settings", padding=10)
        window_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.remember_size_var = tk.BooleanVar(value=self.config.get('UI', 'remember_window_size') == 'true')
        ttk.Checkbutton(window_frame, text="Remember window size", variable=self.remember_size_var).pack(anchor=tk.W)
        
        # Default size
        size_frame = ttk.Frame(window_frame)
        size_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(size_frame, text="Default size:").pack(side=tk.LEFT)
        self.width_var = tk.StringVar(value=self.config.get('UI', 'window_width'))
        ttk.Entry(size_frame, textvariable=self.width_var, width=8).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Label(size_frame, text="×").pack(side=tk.LEFT)
        self.height_var = tk.StringVar(value=self.config.get('UI', 'window_height'))
        ttk.Entry(size_frame, textvariable=self.height_var, width=8).pack(side=tk.LEFT)
    
    def setup_validation_tab(self, parent):
        """Setup validation configuration"""
        validation_frame = ttk.LabelFrame(parent, text="Validation Options", padding=10)
        validation_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.auto_validate_var = tk.BooleanVar(value=self.config.get('Validation', 'auto_validate') == 'true')
        ttk.Checkbutton(validation_frame, text="Auto-validate while editing", variable=self.auto_validate_var).pack(anchor=tk.W)
        
        self.check_refs_var = tk.BooleanVar(value=self.config.get('Validation', 'check_references') == 'true')
        ttk.Checkbutton(validation_frame, text="Check item references", variable=self.check_refs_var).pack(anchor=tk.W)
        
        self.validate_save_var = tk.BooleanVar(value=self.config.get('Validation', 'validate_on_save') == 'true')
        ttk.Checkbutton(validation_frame, text="Validate before saving", variable=self.validate_save_var).pack(anchor=tk.W)
    
    def browse_vanilla_path(self):
        """Browse for vanilla scripts path"""
        path = filedialog.askdirectory(title="Select Project Zomboid media/scripts directory")
        if path:
            self.vanilla_path_var.set(path)
    
    def browse_output_path(self):
        """Browse for output path"""
        path = filedialog.askdirectory(title="Select mod output directory")
        if path:
            self.output_path_var.set(path)
    
    def auto_detect_vanilla(self):
        """Auto-detect vanilla installation"""
        detected_path = self.config.auto_detect_pz_path()
        if detected_path:
            self.vanilla_path_var.set(str(detected_path))
            messagebox.showinfo("Auto-Detect", f"Found Project Zomboid installation at:\n{detected_path}")
        else:
            messagebox.showwarning("Auto-Detect", "Could not automatically detect Project Zomboid installation.\nPlease select the path manually.")
    
    def apply_settings(self):
        """Apply settings without closing"""
        # Save paths
        self.config.set('Paths', 'vanilla_scripts', self.vanilla_path_var.get())
        self.config.set('Paths', 'mod_output', self.output_path_var.get())
        
        # Save UI settings
        self.config.set('UI', 'remember_window_size', str(self.remember_size_var.get()).lower())
        self.config.set('UI', 'window_width', self.width_var.get())
        self.config.set('UI', 'window_height', self.height_var.get())
        
        # Save validation settings
        self.config.set('Validation', 'auto_validate', str(self.auto_validate_var.get()).lower())
        self.config.set('Validation', 'check_references', str(self.check_refs_var.get()).lower())
        self.config.set('Validation', 'validate_on_save', str(self.validate_save_var.get()).lower())
        
        # Reload vanilla database if path changed
        new_vanilla_path = Path(self.vanilla_path_var.get()) if self.vanilla_path_var.get() else None
        current_path = self.config.get_vanilla_scripts_path()
        
        if new_vanilla_path != current_path:
            self.app.load_vanilla_database()
            if hasattr(self.app, 'refresh_vanilla_list'):
                self.app.refresh_vanilla_list()
        
        messagebox.showinfo("Settings", "Settings applied successfully!")
    
    def save_and_close(self):
        """Save settings and close dialog"""
        self.apply_settings()
        self.dialog.destroy()
    
    def open_settings(self):
        """Open settings dialog"""
        SettingsDialog(self.root, self.config, self)
    
    def refresh_vanilla_list(self):
        """Refresh the vanilla items list"""
        if not self.vanilla_db:
            return
        
        # Clear existing items
        for item in self.vanilla_tree.get_children():
            self.vanilla_tree.delete(item)
        
        # Get search criteria
        search_query = getattr(self, 'vanilla_search_var', tk.StringVar()).get().lower()
        type_filter = getattr(self, 'vanilla_type_var', tk.StringVar()).get()
        
        # Filter items
        for name, item in self.vanilla_db.items.items():
            # Type filter
            if type_filter != 'All' and item.get('Type', '') != type_filter:
                continue
            
            # Search filter
            if search_query and search_query not in name.lower():
                continue
            
            # Add to tree
            item_type = item.get('Type', 'Unknown')
            module = item.get('_module', 'Unknown')
            self.vanilla_tree.insert("", tk.END, text=name, values=(item_type, module))
    
    def on_vanilla_search(self, *args):
        """Handle vanilla item search"""
        self.refresh_vanilla_list()
    
    def on_vanilla_selected(self, event):
        """Handle vanilla item selection"""
        selected = self.vanilla_tree.selection()
        if selected:
            item_name = self.vanilla_tree.item(selected[0])['text']
            if item_name in self.vanilla_db.items:
                # Show item properties in form (read-only preview)
                item_data = self.vanilla_db.items[item_name].copy()
                # Remove internal properties
                for key in list(item_data.keys()):
                    if key.startswith('_'):
                        del item_data[key]
                
                self.item_name_var.set(item_name)
                self.create_param_widgets(item_data, readonly=True)
    
    def copy_vanilla_item(self):
        """Copy selected vanilla item to mod"""
        selected = self.vanilla_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a vanilla item to copy")
            return
        
        item_name = self.vanilla_tree.item(selected[0])['text']
        if item_name not in self.vanilla_db.items:
            return
        
        # Get base name without module
        base_name = item_name.split('.')[-1]
        
        # Create unique name
        new_name = base_name
        counter = 1
        while new_name in self.current_mod:
            new_name = f"{base_name}Copy{counter}"
            counter += 1
        
        # Copy item data (remove internal properties)
        item_data = self.vanilla_db.items[item_name].copy()
        for key in list(item_data.keys()):
            if key.startswith('_'):
                del item_data[key]
        
        self.current_mod[new_name] = item_data
        self.refresh_items_list()
        self.status_var.set(f"Copied vanilla item: {item_name} → {new_name}")
    
    def create_vanilla_patch(self):
        """Create a patch for selected vanilla item"""
        selected = self.vanilla_tree.selectionimport tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
import re
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import configparser
from pathlib import Path

@dataclass
class ItemTemplate:
    """Template for different item types with their common parameters"""
    name: str
    type_value: str
    required_params: List[str] = field(default_factory=list)
    optional_params: Dict[str, Any] = field(default_factory=dict)
    description: str = ""

class ConfigManager:
    """Manage application configuration"""
    
    def __init__(self):
        self.config_file = Path("pz_mod_builder_config.ini")
        self.config = configparser.ConfigParser()
        self.load_config()
    
    def load_config(self):
        """Load configuration from file or create defaults"""
        if self.config_file.exists():
            self.config.read(self.config_file)
        else:
            self.create_default_config()
            self.save_config()
    
    def create_default_config(self):
        """Create default configuration"""
        self.config['Paths'] = {
            'vanilla_scripts': '',  # Will be auto-detected or set by user
            'mod_output': './mods',
            'last_mod_directory': '.'
        }
        
        self.config['UI'] = {
            'window_width': '1400',
            'window_height': '900',
            'remember_window_size': 'true'
        }
        
        self.config['Validation'] = {
            'auto_validate': 'true',
            'check_references': 'true',
            'validate_on_save': 'true'
        }
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                self.config.write(f)
        except Exception as e:
            print(f"Warning: Could not save config: {e}")
    
    def get_vanilla_scripts_path(self) -> Optional[Path]:
        """Get the vanilla scripts path, with fallback logic"""
        # 1. Check config file setting
        configured_path = self.config.get('Paths', 'vanilla_scripts', fallback='')
        if configured_path and Path(configured_path).exists():
            return Path(configured_path)
        
        # 2. Check local media/scripts folder
        local_path = Path('./media/scripts')
        if local_path.exists():
            return local_path
        
        # 3. Try to auto-detect common PZ installation paths
        auto_detected = self.auto_detect_pz_path()
        if auto_detected:
            # Save the auto-detected path for future use
            self.config.set('Paths', 'vanilla_scripts', str(auto_detected))
            self.save_config()
            return auto_detected
        
        return None
    
    def auto_detect_pz_path(self) -> Optional[Path]:
        """Try to auto-detect Project Zomboid installation"""
        common_paths = [
            # Windows Steam
            Path.home() / "Steam/steamapps/common/ProjectZomboid/media/scripts",
            Path("C:/Program Files (x86)/Steam/steamapps/common/ProjectZomboid/media/scripts"),
            Path("C:/Steam/steamapps/common/ProjectZomboid/media/scripts"),
            
            # Linux Steam
            Path.home() / ".steam/steam/steamapps/common/ProjectZomboid/media/scripts",
            Path.home() / ".local/share/Steam/steamapps/common/ProjectZomboid/media/scripts",
            
            # Epic Games
            Path("C:/Program Files/Epic Games/ProjectZomboid/media/scripts"),
            
            # GOG
            Path("C:/GOG Games/Project Zomboid/media/scripts"),
            
            # Mac Steam
            Path.home() / "Library/Application Support/Steam/steamapps/common/ProjectZomboid/media/scripts"
        ]
        
        for path in common_paths:
            if path.exists() and path.is_dir():
                # Verify it's actually PZ scripts by checking for known files
                if (path / "items_base.txt").exists() or any(path.glob("items_*.txt")):
                    return path
        
        return None
    
    def set_vanilla_scripts_path(self, path: str):
        """Set the vanilla scripts path"""
        self.config.set('Paths', 'vanilla_scripts', path)
        self.save_config()
    
    def get(self, section: str, key: str, fallback: str = '') -> str:
        """Get a config value"""
        return self.config.get(section, key, fallback=fallback)
    
    def set(self, section: str, key: str, value: str):
        """Set a config value"""
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, value)
        self.save_config()

class VanillaDatabase:
    """Parse and manage vanilla Project Zomboid scripts"""
    
    def __init__(self, scripts_path: Path):
        self.scripts_path = scripts_path
        self.items = {}
        self.recipes = {}
        self.loaded = False
    
    def load_all_scripts(self):
        """Load all vanilla scripts"""
        if not self.scripts_path.exists():
            raise FileNotFoundError(f"Scripts path not found: {self.scripts_path}")
        
        # Load items
        for item_file in self.scripts_path.glob("items_*.txt"):
            self.load_items_file(item_file)
        
        # Load recipes  
        for recipe_file in self.scripts_path.glob("recipes_*.txt"):
            self.load_recipes_file(recipe_file)
        
        self.loaded = True
    
    def load_items_file(self, file_path: Path):
        """Parse a vanilla items file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse module blocks
            module_pattern = r'module\s+(\w+)\s*\{(.*?)\}'
            modules = re.findall(module_pattern, content, re.DOTALL)
            
            for module_name, module_content in modules:
                # Parse item blocks within module
                item_pattern = r'item\s+(\w+)\s*\{(.*?)\}'
                items = re.findall(item_pattern, module_content, re.DOTALL)
                
                for item_name, item_content in items:
                    full_name = f"{module_name}.{item_name}"
                    self.items[full_name] = self.parse_item_properties(item_content)
                    self.items[full_name]['_module'] = module_name
                    self.items[full_name]['_source_file'] = file_path.name
        
        except Exception as e:
            print(f"Warning: Could not parse {file_path}: {e}")
    
    def load_recipes_file(self, file_path: Path):
        """Parse a vanilla recipes file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse module blocks
            module_pattern = r'module\s+(\w+)\s*\{(.*?)\}'
            modules = re.findall(module_pattern, content, re.DOTALL)
            
            for module_name, module_content in modules:
                # Parse recipe blocks
                recipe_pattern = r'recipe\s+([^{]+)\{(.*?)\}'
                recipes = re.findall(recipe_pattern, module_content, re.DOTALL)
                
                for recipe_name, recipe_content in recipes:
                    recipe_name = recipe_name.strip()
                    self.recipes[recipe_name] = self.parse_recipe_properties(recipe_content)
                    self.recipes[recipe_name]['_module'] = module_name
                    self.recipes[recipe_name]['_source_file'] = file_path.name
        
        except Exception as e:
            print(f"Warning: Could not parse {file_path}: {e}")
    
    def parse_item_properties(self, content: str) -> Dict[str, Any]:
        """Parse item properties from content"""
        properties = {}
        
        # Match property = value, patterns
        property_pattern = r'(\w+)\s*=\s*([^,\n]+),'
        matches = re.findall(property_pattern, content)
        
        for prop, value in matches:
            # Clean up the value
            value = value.strip()
            
            # Convert to appropriate types
            if value.upper() in ['TRUE', 'FALSE']:
                properties[prop] = value.upper() == 'TRUE'
            elif value.replace('.', '').replace('-', '').isdigit():
                properties[prop] = float(value) if '.' in value else int(value)
            else:
                properties[prop] = value
        
        return properties
    
    def parse_recipe_properties(self, content: str) -> Dict[str, Any]:
        """Parse recipe properties from content"""
        properties = {}
        lines = content.strip().split('\n')
        
        inputs = []
        in_inputs = True
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('//'):
                continue
            
            # Check if this is a property line (contains :)
            if ':' in line and not line.startswith('keep ') and not '/' in line:
                in_inputs = False
                prop, value = line.split(':', 1)
                prop = prop.strip()
                value = value.strip().rstrip(',')
                properties[prop] = value
            elif in_inputs and line and not ':' in line:
                # This is an input item
                inputs.append(line.rstrip(','))
        
        properties['_inputs'] = inputs
        return properties
    
    def search_items(self, query: str = '', item_type: str = '') -> Dict[str, Dict]:
        """Search items by name or type"""
        if not self.loaded:
            return {}
        
        results = {}
        query_lower = query.lower()
        
        for name, item in self.items.items():
            # Filter by type if specified
            if item_type and item.get('Type', '').lower() != item_type.lower():
                continue
            
            # Filter by query if specified
            if query and query_lower not in name.lower():
                continue
            
            results[name] = item
        
        return results
    
    def get_item_categories(self) -> Dict[str, List[str]]:
        """Get items organized by category"""
        categories = {}
        
        for name, item in self.items.items():
            item_type = item.get('Type', 'Unknown')
            if item_type not in categories:
                categories[item_type] = []
            categories[item_type].append(name)
        
        return categories

class ProjectZomboidModBuilder:
    def __init__(self, root):
        self.root = root
        self.root.title("Project Zomboid Mod Builder")
        
        # Initialize configuration
        self.config = ConfigManager()
        
        # Set window size from config
        width = self.config.get('UI', 'window_width', '1400')
        height = self.config.get('UI', 'window_height', '900')
        self.root.geometry(f"{width}x{height}")
        
        # Current mod data
        self.current_mod = {}
        self.current_file_path = None
        
        # Vanilla database
        self.vanilla_db = None
        self.load_vanilla_database()
        
        # Templates for different script types
        self.templates = self._load_templates()
        
        self.setup_ui()
    
    def load_vanilla_database(self):
        """Load vanilla Project Zomboid database"""
        vanilla_path = self.config.get_vanilla_scripts_path()
        
        if vanilla_path:
            try:
                self.vanilla_db = VanillaDatabase(vanilla_path)
                self.vanilla_db.load_all_scripts()
                print(f"Loaded {len(self.vanilla_db.items)} vanilla items and {len(self.vanilla_db.recipes)} recipes")
            except Exception as e:
                self.vanilla_db = None
                messagebox.showwarning(
                    "Vanilla Scripts Not Found", 
                    f"Could not load vanilla scripts from:\n{vanilla_path}\n\n"
                    f"Error: {e}\n\n"
                    f"You can configure the path in Settings menu."
                )
        else:
            messagebox.showinfo(
                "Configure Vanilla Scripts", 
                "Vanilla scripts path not found.\n\n"
                "Please configure the path to your Project Zomboid installation\n"
                "in the Settings menu to enable vanilla item browsing and patching."
            )
        
    def _load_templates(self) -> Dict[str, ItemTemplate]:
        """Load predefined templates for different item types"""
        return {
            "weapon_melee": ItemTemplate(
                name="Melee Weapon",
                type_value="Weapon",
                required_params=["DisplayName", "Icon", "Weight", "Type"],
                optional_params={
                    "DisplayCategory": "Weapon",
                    "SubCategory": "Swinging",
                    "Categories": "Axe",
                    "MinDamage": 0.5,
                    "MaxDamage": 1.5,
                    "BaseSpeed": 1.0,
                    "CriticalChance": 10,
                    "CritDmgMultiplier": 3.0,
                    "MinRange": 0.61,
                    "MaxRange": 1.1,
                    "SwingTime": 4,
                    "SwingAnim": "Bat",
                    "WeaponSprite": "",
                    "AttachmentType": "Hammer",
                    "ConditionMax": 10,
                    "ConditionLowerChanceOneIn": 10,
                    "DoorDamage": 5,
                    "TreeDamage": 0,
                    "SwingSound": "",
                    "HitSound": "",
                    "BreakSound": "",
                    "Tags": ""
                },
                description="A melee weapon like axe, sword, or club"
            ),
            "weapon_ranged": ItemTemplate(
                name="Ranged Weapon",
                type_value="Weapon",
                required_params=["DisplayName", "Icon", "Weight", "Type"],
                optional_params={
                    "DisplayCategory": "Weapon",
                    "SubCategory": "Firearm",
                    "Categories": "Rifle",
                    "MinDamage": 1.0,
                    "MaxDamage": 3.0,
                    "BaseSpeed": 0.8,
                    "CriticalChance": 20,
                    "CritDmgMultiplier": 4.0,
                    "MinRange": 3.0,
                    "MaxRange": 10.0,
                    "WeaponSprite": "",
                    "AttachmentType": "Rifle",
                    "ConditionMax": 10,
                    "AimingTime": 40,
                    "ReloadTime": 30,
                    "ClipSize": 10,
                    "AmmoType": "Base.223Bullets",
                    "FireMode": "Single",
                    "Tags": ""
                },
                description="A ranged weapon like pistol, rifle, or bow"
            ),
            "food": ItemTemplate(
                name="Food Item",
                type_value="Food",
                required_params=["DisplayName", "Icon", "Weight", "Type"],
                optional_params={
                    "DisplayCategory": "Food",
                    "HungerChange": -10,
                    "ThirstChange": 0,
                    "Calories": 100,
                    "Carbohydrates": 10,
                    "Lipids": 5,
                    "Proteins": 8,
                    "DaysFresh": 3,
                    "DaysTotallyRotten": 7,
                    "IsCookable": "FALSE",
                    "MinutesToCook": 0,
                    "MinutesToBurn": 0,
                    "Alcoholic": "FALSE",
                    "BoredomChange": 0,
                    "UnhappyChange": 0,
                    "Tags": ""
                },
                description="An edible food item"
            ),
            "clothing": ItemTemplate(
                name="Clothing Item",
                type_value="Clothing",
                required_params=["DisplayName", "Icon", "Weight", "Type", "BodyLocation", "CanBeEquipped"],
                optional_params={
                    "DisplayCategory": "Clothing",
                    "ClothingItem": "",
                    "ScratchDefense": 0,
                    "BiteDefense": 0,
                    "BulletDefense": 0,
                    "BluntDefense": 0,
                    "Insulation": 0.0,
                    "WindResistance": 0.0,
                    "WaterResistance": 0,
                    "FabricType": "Cotton",
                    "Tags": ""
                },
                description="Wearable clothing item"
            ),
            "container": ItemTemplate(
                name="Container",
                type_value="Container",
                required_params=["DisplayName", "Icon", "Weight", "Type"],
                optional_params={
                    "DisplayCategory": "Container",
                    "Capacity": 10,
                    "WeightReduction": 50,
                    "CanBeEquipped": "Back",
                    "AttachmentType": "Bag",
                    "Tags": ""
                },
                description="A storage container like bag or box"
            ),
            "tool": ItemTemplate(
                name="Tool",
                type_value="Normal",
                required_params=["DisplayName", "Icon", "Weight", "Type"],
                optional_params={
                    "DisplayCategory": "Tools",
                    "MetalValue": 10,
                    "ConditionMax": 10,
                    "ConditionLowerChanceOneIn": 20,
                    "Tags": "CraftingTool"
                },
                description="A utility tool"
            )
        }
    
    def setup_ui(self):
        """Setup the main UI"""
        # Create main menu
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)
        
        file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Mod", command=self.new_mod)
        file_menu.add_command(label="Open Mod", command=self.open_mod)
        file_menu.add_command(label="Save Mod", command=self.save_mod)
        file_menu.add_command(label="Save As...", command=self.save_mod_as)
        file_menu.add_separator()
        file_menu.add_command(label="Export Script", command=self.export_script)
        file_menu.add_separator()
        file_menu.add_command(label="Settings", command=self.open_settings)
        
        # Create main paned window
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Template selection and item list
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=1)
        
        # Add notebook for left panel
        left_notebook = ttk.Notebook(left_frame)
        left_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Templates tab
        templates_frame = ttk.Frame(left_notebook)
        left_notebook.add(templates_frame, text="Templates")
        
        # Vanilla browser tab
        vanilla_frame = ttk.Frame(left_notebook)
        left_notebook.add(vanilla_frame, text="Vanilla Items")
        
        # Mod items tab
        mod_items_frame = ttk.Frame(left_notebook)
        left_notebook.add(mod_items_frame, text="Mod Items")
        
        self.setup_templates_tab(templates_frame)
        self.setup_vanilla_tab(vanilla_frame)
        self.setup_mod_items_tab(mod_items_frame)
        
        # Right panel - Item editor
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=2)
        
        # Create notebook for different views
        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Form editor tab
        self.form_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.form_frame, text="Form Editor")
        
        # Script preview tab
        self.preview_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.preview_frame, text="Script Preview")
        
        self.setup_form_editor()
        self.setup_script_preview()
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready - Vanilla database loaded" if self.vanilla_db else "Ready - No vanilla database")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def setup_templates_tab(self, parent):
        """Setup the templates tab"""
        # Template selection
        ttk.Label(parent, text="Item Templates:", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        template_frame = ttk.Frame(parent)
        template_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.template_var = tk.StringVar()
        template_combo = ttk.Combobox(template_frame, textvariable=self.template_var, 
                                     values=list(self.templates.keys()), state="readonly")
        template_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        template_combo.bind("<<ComboboxSelected>>", self.on_template_selected)
        
        ttk.Button(template_frame, text="Add Item", command=self.add_item).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Template description
        self.template_desc = ttk.Label(parent, text="Select a template to see description", 
                                      wraplength=300, justify=tk.LEFT)
        self.template_desc.pack(anchor=tk.W, pady=(0, 10))
    
    def setup_vanilla_tab(self, parent):
        """Setup the vanilla items browser tab"""
        if not self.vanilla_db:
            ttk.Label(parent, text="Vanilla database not loaded.\nConfigure path in Settings.", 
                     justify=tk.CENTER).pack(expand=True)
            return
        
        # Search frame
        search_frame = ttk.Frame(parent)
        search_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.vanilla_search_var = tk.StringVar()
        self.vanilla_search_var.trace('w', self.on_vanilla_search)
        search_entry = ttk.Entry(search_frame, textvariable=self.vanilla_search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # Category filter
        ttk.Label(search_frame, text="Type:").pack(side=tk.LEFT, padx=(10, 5))
        self.vanilla_type_var = tk.StringVar()
        type_combo = ttk.Combobox(search_frame, textvariable=self.vanilla_type_var, width=15)
        
        # Get all item types from vanilla database
        all_types = set()
        for item in self.vanilla_db.items.values():
            item_type = item.get('Type', 'Unknown')
            all_types.add(item_type)
        
        type_combo['values'] = ['All'] + sorted(list(all_types))
        type_combo.set('All')
        type_combo.bind("<<ComboboxSelected>>", self.on_vanilla_search)
        type_combo.pack(side=tk.LEFT)
        
        # Vanilla items tree
        vanilla_tree_frame = ttk.Frame(parent)
        vanilla_tree_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        self.vanilla_tree = ttk.Treeview(vanilla_tree_frame, columns=("Type", "Module"), show="tree headings")
        self.vanilla_tree.heading("#0", text="Item Name")
        self.vanilla_tree.heading("Type", text="Type")
        self.vanilla_tree.heading("Module", text="Module")
        self.vanilla_tree.column("#0", width=200)
        self.vanilla_tree.column("Type", width=100)
        self.vanilla_tree.column("Module", width=80)
        
        vanilla_scrollbar = ttk.Scrollbar(vanilla_tree_frame, orient=tk.VERTICAL, command=self.vanilla_tree.yview)
        self.vanilla_tree.configure(yscrollcommand=vanilla_scrollbar.set)
        
        self.vanilla_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vanilla_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.vanilla_tree.bind("<<TreeviewSelect>>", self.on_vanilla_selected)
        
        # Vanilla item actions
        vanilla_actions = ttk.Frame(parent)
        vanilla_actions.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(vanilla_actions, text="Copy to Mod", command=self.copy_vanilla_item).pack(side=tk.LEFT)
        ttk.Button(vanilla_actions, text="Create Patch", command=self.create_vanilla_patch).pack(side=tk.LEFT, padx=(5, 0))
        
        # Load initial vanilla items
        self.refresh_vanilla_list()
    
    def setup_mod_items_tab(self, parent):
        """Setup the mod items tab"""
        # Items list
        ttk.Label(parent, text="Mod Items:", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        items_frame = ttk.Frame(parent)
        items_frame.pack(fill=tk.BOTH, expand=True)
        
        self.items_tree = ttk.Treeview(items_frame, columns=("Type",), show="tree headings")
        self.items_tree.heading("#0", text="Item Name")
        self.items_tree.heading("Type", text="Type")
        self.items_tree.column("#0", width=200)
        self.items_tree.column("Type", width=100)
        
        items_scrollbar = ttk.Scrollbar(items_frame, orient=tk.VERTICAL, command=self.items_tree.yview)
        self.items_tree.configure(yscrollcommand=items_scrollbar.set)
        
        self.items_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        items_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.items_tree.bind("<<TreeviewSelect>>", self.on_item_selected)
        
        # Item action buttons
        item_buttons_frame = ttk.Frame(parent)
        item_buttons_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(item_buttons_frame, text="Duplicate", command=self.duplicate_item).pack(side=tk.LEFT)
        ttk.Button(item_buttons_frame, text="Delete", command=self.delete_item).pack(side=tk.LEFT, padx=(5, 0))
        
    def setup_form_editor(self):
        """Setup the form editor with scrollable parameter fields"""
        # Item name and basic info
        basic_frame = ttk.LabelFrame(self.form_frame, text="Basic Information", padding=10)
        basic_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(basic_frame, text="Item Name:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.item_name_var = tk.StringVar()
        self.item_name_var.trace('w', self.on_item_name_changed)
        ttk.Entry(basic_frame, textvariable=self.item_name_var, width=30).grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(basic_frame, text="Module Name:").grid(row=0, column=2, sticky=tk.W, padx=(20, 5))
        self.module_name_var = tk.StringVar(value="Base")
        ttk.Entry(basic_frame, textvariable=self.module_name_var, width=20).grid(row=0, column=3, sticky=tk.W)
        
        # Scrollable parameters frame
        params_frame = ttk.LabelFrame(self.form_frame, text="Parameters", padding=10)
        params_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create scrollable canvas
        canvas = tk.Canvas(params_frame)
        scrollbar = ttk.Scrollbar(params_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel to canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<MouseWheel>", _on_mousewheel)
        
        self.param_vars = {}
        self.param_widgets = {}
        
    def setup_script_preview(self):
        """Setup the script preview tab"""
        preview_toolbar = ttk.Frame(self.preview_frame)
        preview_toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(preview_toolbar, text="Refresh Preview", command=self.update_preview).pack(side=tk.LEFT)
        ttk.Button(preview_toolbar, text="Copy to Clipboard", command=self.copy_to_clipboard).pack(side=tk.LEFT, padx=(5, 0))
        
        self.preview_text = scrolledtext.ScrolledText(self.preview_frame, wrap=tk.WORD, font=("Consolas", 10))
        self.preview_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def new_mod(self):
        """Create a new mod"""
        if self.current_mod and messagebox.askyesno("New Mod", "Discard current mod and create new one?"):
            self.current_mod = {}
            self.current_file_path = None
            self.refresh_items_list()
            self.clear_form()
            self.status_var.set("New mod created")
    
    def open_mod(self):
        """Open an existing mod file"""
        file_path = filedialog.askopenfilename(
            title="Open Mod File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.current_mod = json.load(f)
                self.current_file_path = file_path
                self.refresh_items_list()
                self.clear_form()
                self.status_var.set(f"Loaded: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load mod file:\n{str(e)}")
    
    def save_mod(self):
        """Save current mod"""
        if not self.current_file_path:
            self.save_mod_as()
        else:
            self._save_to_file(self.current_file_path)
    
    def save_mod_as(self):
        """Save mod as new file"""
        file_path = filedialog.asksaveasfilename(
            title="Save Mod As",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            self._save_to_file(file_path)
            self.current_file_path = file_path
    
    def _save_to_file(self, file_path):
        """Save mod data to file"""
        try:
            # Save current item if being edited
            self.save_current_item()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.current_mod, f, indent=2, ensure_ascii=False)
            self.status_var.set(f"Saved: {os.path.basename(file_path)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save mod file:\n{str(e)}")
    
    def export_script(self):
        """Export as Project Zomboid script"""
        if not self.current_mod:
            messagebox.showwarning("Warning", "No mod data to export")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Export Script",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            try:
                script = self.generate_script()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(script)
                self.status_var.set(f"Script exported: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export script:\n{str(e)}")
    
    def on_template_selected(self, event):
        """Handle template selection"""
        template_key = self.template_var.get()
        if template_key in self.templates:
            template = self.templates[template_key]
            self.status_var.set(f"Selected template: {template.description}")
    
    def add_item(self):
        """Add a new item based on selected template"""
        template_key = self.template_var.get()
        if not template_key:
            messagebox.showwarning("Warning", "Please select a template first")
            return
        
        template = self.templates[template_key]
        
        # Create unique item name
        base_name = f"New{template.name.replace(' ', '')}"
        item_name = base_name
        counter = 1
        while item_name in self.current_mod:
            item_name = f"{base_name}{counter}"
            counter += 1
        
        # Create item data from template
        item_data = {
            "Type": template.type_value,
            **template.optional_params
        }
        
        self.current_mod[item_name] = item_data
        self.refresh_items_list()
        
        # Select the new item
        for item_id in self.items_tree.get_children():
            if self.items_tree.item(item_id)['text'] == item_name:
                self.items_tree.selection_set(item_id)
                self.items_tree.focus(item_id)
                break
        
        self.status_var.set(f"Added item: {item_name}")
    
    def duplicate_item(self):
        """Duplicate selected item"""
        selected = self.items_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an item to duplicate")
            return
        
        item_name = self.items_tree.item(selected[0])['text']
        if item_name not in self.current_mod:
            return
        
        # Create unique name
        base_name = f"{item_name}Copy"
        new_name = base_name
        counter = 1
        while new_name in self.current_mod:
            new_name = f"{base_name}{counter}"
            counter += 1
        
        # Duplicate item data
        self.current_mod[new_name] = self.current_mod[item_name].copy()
        self.refresh_items_list()
        self.status_var.set(f"Duplicated item: {new_name}")
    
    def delete_item(self):
        """Delete selected item"""
        selected = self.items_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an item to delete")
            return
        
        item_name = self.items_tree.item(selected[0])['text']
        if item_name in self.current_mod:
            if messagebox.askyesno("Confirm Delete", f"Delete item '{item_name}'?"):
                del self.current_mod[item_name]
                self.refresh_items_list()
                self.clear_form()
                self.status_var.set(f"Deleted item: {item_name}")
    
    def refresh_items_list(self):
        """Refresh the items tree view"""
        for item in self.items_tree.get_children():
            self.items_tree.delete(item)
        
        for item_name, item_data in self.current_mod.items():
            item_type = item_data.get("Type", "Unknown")
            self.items_tree.insert("", tk.END, text=item_name, values=(item_type,))
    
    def on_item_selected(self, event):
        """Handle item selection in tree"""
        selected = self.items_tree.selection()
        if selected:
            item_name = self.items_tree.item(selected[0])['text']
            if item_name in self.current_mod:
                self.load_item_in_form(item_name, self.current_mod[item_name])
    
    def on_item_name_changed(self, *args):
        """Handle item name change"""
        # Update the tree view if an item is selected
        selected = self.items_tree.selection()
        if selected:
            old_name = self.items_tree.item(selected[0])['text']
            new_name = self.item_name_var.get()
            if new_name and new_name != old_name and old_name in self.current_mod:
                # Rename the item
                self.current_mod[new_name] = self.current_mod.pop(old_name)
                self.items_tree.item(selected[0], text=new_name)
    
    def load_item_in_form(self, item_name, item_data):
        """Load item data into the form"""
        self.item_name_var.set(item_name)
        self.create_param_widgets(item_data)
        self.update_preview()
    
    def create_param_widgets(self, item_data):
        """Create parameter widgets based on item data"""
        # Clear existing widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        self.param_vars.clear()
        self.param_widgets.clear()
        
        row = 0
        for param, value in sorted(item_data.items()):
            # Create label
            label = ttk.Label(self.scrollable_frame, text=f"{param}:", width=20, anchor=tk.W)
            label.grid(row=row, column=0, sticky=tk.W, padx=(0, 10), pady=2)
            
            # Create appropriate widget based on parameter type
            var = self.create_param_var(param, value)
            widget = self.create_param_widget(param, value, var)
            widget.grid(row=row, column=1, sticky=tk.W, pady=2)
            
            self.param_vars[param] = var
            self.param_widgets[param] = widget
            
            row += 1
        
        # Add button to add new parameter
        add_param_frame = ttk.Frame(self.scrollable_frame)
        add_param_frame.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=10)
        
        ttk.Button(add_param_frame, text="Add Parameter", command=self.add_parameter).pack(side=tk.LEFT)
        ttk.Button(add_param_frame, text="Update Preview", command=self.update_preview).pack(side=tk.LEFT, padx=(5, 0))
    
    def create_param_var(self, param, value):
        """Create appropriate tkinter variable for parameter"""
        if isinstance(value, bool):
            var = tk.BooleanVar(value=value)
        elif isinstance(value, (int, float)):
            var = tk.StringVar(value=str(value))
        else:
            var = tk.StringVar(value=str(value))
        
        # Bind to update preview when changed
        var.trace('w', lambda *args: self.update_preview())
        return var
    
    def create_param_widget(self, param, value, var):
        """Create appropriate widget for parameter"""
        frame = ttk.Frame(self.scrollable_frame)
        
        if isinstance(value, bool):
            widget = ttk.Checkbutton(frame, variable=var)
            widget.pack(side=tk.LEFT)
        elif param in ["DisplayCategory", "SubCategory", "Categories", "BodyLocation", "AttachmentType"]:
            # Use combobox for common categorical parameters
            common_values = self.get_common_values(param)
            widget = ttk.Combobox(frame, textvariable=var, values=common_values, width=30)
            widget.pack(side=tk.LEFT)
        else:
            widget = ttk.Entry(frame, textvariable=var, width=30)
            widget.pack(side=tk.LEFT)
        
        # Add delete button for each parameter
        delete_btn = ttk.Button(frame, text="×", width=3, 
                               command=lambda p=param: self.delete_parameter(p))
        delete_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        return frame
    
    def get_common_values(self, param):
        """Get common values for categorical parameters"""
        common_values = {
            "DisplayCategory": ["Weapon", "Food", "Clothing", "Container", "Tools", "Medical", "Literature"],
            "SubCategory": ["Swinging", "LongBlade", "SmallBlade", "Spear", "Firearm"],
            "Categories": ["Axe", "Blade", "Blunt", "Rifle", "Pistol"],
            "BodyLocation": ["Torso_Upper", "Torso_Lower", "Head", "Hands", "Feet", "Legs", "Back"],
            "AttachmentType": ["Hammer", "Shovel", "Rifle", "Bag", "BigWeapon"]
        }
        return common_values.get(param, [])
    
    def add_parameter(self):
        """Add a new parameter to current item"""
        dialog = ParameterDialog(self.root)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            param_name, param_value = dialog.result
            selected = self.items_tree.selection()
            if selected:
                item_name = self.items_tree.item(selected[0])['text']
                if item_name in self.current_mod:
                    self.current_mod[item_name][param_name] = param_value
                    self.load_item_in_form(item_name, self.current_mod[item_name])
    
    def delete_parameter(self, param):
        """Delete a parameter from current item"""
        if messagebox.askyesno("Confirm Delete", f"Delete parameter '{param}'?"):
            selected = self.items_tree.selection()
            if selected:
                item_name = self.items_tree.item(selected[0])['text']
                if item_name in self.current_mod and param in self.current_mod[item_name]:
                    del self.current_mod[item_name][param]
                    self.load_item_in_form(item_name, self.current_mod[item_name])
    
    def save_current_item(self):
        """Save current form data to item"""
        selected = self.items_tree.selection()
        if selected and self.param_vars:
            item_name = self.item_name_var.get()
            old_name = self.items_tree.item(selected[0])['text']
            
            if old_name in self.current_mod:
                # Collect current form data
                item_data = {}
                for param, var in self.param_vars.items():
                    value = var.get()
                    # Convert string values to appropriate types
                    if value.lower() in ['true', 'false']:
                        value = value.lower() == 'true'
                    elif value.replace('.', '').replace('-', '').isdigit():
                        value = float(value) if '.' in value else int(value)
                    item_data[param] = value
                
                # Handle item rename
                if item_name != old_name:
                    del self.current_mod[old_name]
                
                self.current_mod[item_name] = item_data
    
    def clear_form(self):
        """Clear the form"""
        self.item_name_var.set("")
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.param_vars.clear()
        self.param_widgets.clear()
        self.preview_text.delete(1.0, tk.END)
    
    def update_preview(self):
        """Update the script preview"""
        try:
            script = self.generate_script()
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(1.0, script)
        except Exception as e:
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(1.0, f"Error generating preview:\n{str(e)}")
    
    def generate_script(self):
        """Generate Project Zomboid script from current mod data"""
        if not self.current_mod:
            return "// No items defined"
        
        # Save current item first
        self.save_current_item()
        
        module_name = self.module_name_var.get() or "Base"
        
        script_lines = [
            f"module {module_name}",
            "{",
            ""
        ]
        
        for item_name, item_data in self.current_mod.items():
            script_lines.extend(self.generate_item_script(item_name, item_data))
            script_lines.append("")
        
        script_lines.append("}")
        
        return "\n".join(script_lines)
    
    def generate_item_script(self, item_name, item_data):
        """Generate script lines for a single item"""
        lines = [
            f"\titem {item_name}",
            "\t{"
        ]
        
        # Sort parameters for consistent output
        for param, value in sorted(item_data.items()):
            if isinstance(value, bool):
                value_str = "TRUE" if value else "FALSE"
            elif isinstance(value, str):
                value_str = value
            else:
                value_str = str(value)
            
            lines.append(f"\t\t{param} = {value_str},")
        
        lines.append("\t}")
        
        return lines
    
    def copy_to_clipboard(self):
        """Copy script preview to clipboard"""
        script = self.preview_text.get(1.0, tk.END)
        self.root.clipboard_clear()
        self.root.clipboard_append(script)
        self.status_var.set("Script copied to clipboard")


class ParameterDialog:
    """Dialog for adding new parameters"""
    def __init__(self, parent):
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Add Parameter")
        self.dialog.geometry("400x200")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Parameter name
        ttk.Label(main_frame, text="Parameter Name:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.name_var = tk.StringVar()
        name_combo = ttk.Combobox(main_frame, textvariable=self.name_var, width=30)
        name_combo['values'] = self.get_common_parameters()
        name_combo.grid(row=0, column=1, sticky=tk.W, pady=(0, 5))
        
        # Parameter value
        ttk.Label(main_frame, text="Parameter Value:").grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        self.value_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.value_var, width=30).grid(row=1, column=1, sticky=tk.W, pady=(0, 5))
        
        # Value type
        ttk.Label(main_frame, text="Value Type:").grid(row=2, column=0, sticky=tk.W, pady=(0, 10))
        self.type_var = tk.StringVar(value="String")
        type_combo = ttk.Combobox(main_frame, textvariable=self.type_var, 
                                 values=["String", "Integer", "Float", "Boolean"], 
                                 state="readonly", width=30)
        type_combo.grid(row=2, column=1, sticky=tk.W, pady=(0, 10))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="OK", command=self.ok_clicked).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Cancel", command=self.cancel_clicked).pack(side=tk.LEFT)
    
    def get_common_parameters(self):
        """Get list of common Project Zomboid parameters"""
        return [
            "DisplayName", "Icon", "Weight", "Type", "DisplayCategory",
            "SubCategory", "Categories", "MinDamage", "MaxDamage", "BaseSpeed",
            "CriticalChance", "CritDmgMultiplier", "MinRange", "MaxRange",
            "SwingTime", "SwingAnim", "WeaponSprite", "AttachmentType",
            "ConditionMax", "ConditionLowerChanceOneIn", "DoorDamage",
            "TreeDamage", "SwingSound", "HitSound", "BreakSound", "Tags",
            "HungerChange", "ThirstChange", "Calories", "Carbohydrates",
            "Lipids", "Proteins", "DaysFresh", "DaysTotallyRotten",
            "IsCookable", "Alcoholic", "BoredomChange", "UnhappyChange",
            "BodyLocation", "CanBeEquipped", "ClothingItem", "ScratchDefense",
            "BiteDefense", "BulletDefense", "BluntDefense", "Insulation",
            "WindResistance", "WaterResistance", "FabricType", "Capacity",
            "WeightReduction", "MetalValue", "Tooltip"
        ]
    
    def ok_clicked(self):
        """Handle OK button click"""
        name = self.name_var.get().strip()
        value = self.value_var.get().strip()
        value_type = self.type_var.get()
        
        if not name:
            messagebox.showwarning("Warning", "Please enter a parameter name")
            return
        
        if not value:
            messagebox.showwarning("Warning", "Please enter a parameter value")
            return
        
        # Convert value based on type
        try:
            if value_type == "Integer":
                converted_value = int(value)
            elif value_type == "Float":
                converted_value = float(value)
            elif value_type == "Boolean":
                converted_value = value.lower() in ['true', '1', 'yes', 'on']
            else:
                converted_value = value
            
            self.result = (name, converted_value)
            self.dialog.destroy()
        except ValueError:
            messagebox.showerror("Error", f"Invalid {value_type.lower()} value: {value}")
    
    def cancel_clicked(self):
        """Handle Cancel button click"""
        self.dialog.destroy()


class ValidationDialog:
    """Dialog for script validation using Project Zomboid tools"""
    def __init__(self, parent, mod_builder):
        self.mod_builder = mod_builder
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Script Validation")
        self.dialog.geometry("600x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.setup_ui()
        self.validate_script()
    
    def setup_ui(self):
        """Setup validation dialog UI"""
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="Script Validation Results:", 
                 font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(0, 10))
        
        self.results_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, font=("Consolas", 9))
        self.results_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Re-validate", command=self.validate_script).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Close", command=self.dialog.destroy).pack(side=tk.RIGHT)
    
    def validate_script(self):
        """Validate the current script"""
        self.results_text.delete(1.0, tk.END)
        
        try:
            script = self.mod_builder.generate_script()
            issues = []
            
            # Basic syntax validation
            issues.extend(self.validate_syntax(script))
            
            # Parameter validation
            issues.extend(self.validate_parameters())
            
            # Display results
            if not issues:
                self.results_text.insert(tk.END, "✓ No validation issues found!\n\n")
                self.results_text.insert(tk.END, "Your script appears to be valid.")
            else:
                self.results_text.insert(tk.END, f"Found {len(issues)} validation issues:\n\n")
                for i, issue in enumerate(issues, 1):
                    self.results_text.insert(tk.END, f"{i}. {issue}\n")
        
        except Exception as e:
            self.results_text.insert(tk.END, f"Error during validation: {str(e)}")
    
    def validate_syntax(self, script):
        """Basic syntax validation"""
        issues = []
        lines = script.split('\n')
        
        brace_count = 0
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith('//'):
                continue
            
            # Check brace balance
            brace_count += stripped.count('{') - stripped.count('}')
            
            # Check for common syntax errors
            if stripped.endswith('=') and not stripped.endswith('=='):
                issues.append(f"Line {line_num}: Missing value after '='")
            
            if '=' in stripped and not stripped.endswith(',') and not stripped.endswith('{') and not stripped.endswith('}'):
                if not stripped.startswith('module') and not stripped.startswith('item'):
                    issues.append(f"Line {line_num}: Missing comma after parameter")
        
        if brace_count != 0:
            issues.append(f"Mismatched braces (difference: {brace_count})")
        
        return issues
    
    def validate_parameters(self):
        """Validate item parameters"""
        issues = []
        
        for item_name, item_data in self.mod_builder.current_mod.items():
            # Check required parameters
            if 'Type' not in item_data:
                issues.append(f"Item '{item_name}': Missing required 'Type' parameter")
            
            if 'DisplayName' not in item_data:
                issues.append(f"Item '{item_name}': Missing required 'DisplayName' parameter")
            
            if 'Icon' not in item_data:
                issues.append(f"Item '{item_name}': Missing required 'Icon' parameter")
            
            # Validate weapon-specific parameters
            if item_data.get('Type') == 'Weapon':
                weapon_issues = self.validate_weapon_params(item_name, item_data)
                issues.extend(weapon_issues)
            
            # Validate food-specific parameters
            elif item_data.get('Type') == 'Food':
                food_issues = self.validate_food_params(item_name, item_data)
                issues.extend(food_issues)
        
        return issues
    
    def validate_weapon_params(self, item_name, item_data):
        """Validate weapon-specific parameters"""
        issues = []
        
        # Check damage values
        min_damage = item_data.get('MinDamage', 0)
        max_damage = item_data.get('MaxDamage', 0)
        
        if isinstance(min_damage, (int, float)) and isinstance(max_damage, (int, float)):
            if min_damage > max_damage:
                issues.append(f"Weapon '{item_name}': MinDamage ({min_damage}) is greater than MaxDamage ({max_damage})")
        
        # Check range values
        min_range = item_data.get('MinRange', 0)
        max_range = item_data.get('MaxRange', 0)
        
        if isinstance(min_range, (int, float)) and isinstance(max_range, (int, float)):
            if min_range > max_range:
                issues.append(f"Weapon '{item_name}': MinRange ({min_range}) is greater than MaxRange ({max_range})")
        
        return issues
    
    def validate_food_params(self, item_name, item_data):
        """Validate food-specific parameters"""
        issues = []
        
        # Check spoilage values
        days_fresh = item_data.get('DaysFresh', 0)
        days_rotten = item_data.get('DaysTotallyRotten', 0)
        
        if isinstance(days_fresh, (int, float)) and isinstance(days_rotten, (int, float)):
            if days_fresh > days_rotten and days_rotten > 0:
                issues.append(f"Food '{item_name}': DaysFresh ({days_fresh}) is greater than DaysTotallyRotten ({days_rotten})")
        
        return issues


def main():
    """Main function to run the application"""
    root = tk.Tk()
    
    try:
        # Set application icon if available
        root.iconbitmap("icon.ico")
    except:
        pass  # Icon file not found, continue without it
    
    app = ProjectZomboidModBuilder(root)
    
    # Add Tools menu to the existing menubar
    tools_menu = tk.Menu(app.menubar, tearoff=0)
    app.menubar.add_cascade(label="Tools", menu=tools_menu)
    tools_menu.add_command(label="Validate Script", 
                          command=lambda: ValidationDialog(root, app))
    tools_menu.add_separator()
    tools_menu.add_command(label="Import Vanilla Item", 
                          command=lambda: messagebox.showinfo("Coming Soon", 
                                                             "Import vanilla items functionality coming soon!"))
    
    root.mainloop()


if __name__ == "__main__":
    main()