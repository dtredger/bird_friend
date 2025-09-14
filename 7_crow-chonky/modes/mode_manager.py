"""
ModeManager - Clean BaseMode Architecture with Fixed Module Import
================================================================

Manages mode loading and switching for BaseMode-derived modes only.
Now handles the _mode.py file naming convention properly.

All modes are assumed to:
- Inherit from BaseMode
- Handle their own button presses automatically
- Implement proper cleanup
- Follow the BaseMode lifecycle
"""

from modes.base_mode import BaseMode


class ModeManager:
    """Clean mode manager for BaseMode-derived modes only"""

    def __init__(self, crow, config):
        self.crow = crow
        self.config = config

        # Load available modes from config
        self.available_modes = self._load_available_modes()

        # Current mode setup
        self.current_mode_name = config.get("mode", self.available_modes[0])

        # Validate current mode is available
        if self.current_mode_name not in self.available_modes:
            print(f"⚠️ Mode '{self.current_mode_name}' not available, using first mode")
            self.current_mode_name = self.available_modes[0]

        self.current_mode_instance = None

        # Load initial mode
        self.load_mode(self.current_mode_name)

    def _load_available_modes(self):
        """Load available modes from config"""
        available_modes = self.config.get("available_modes", [])

        if not isinstance(available_modes, list):
            print("⚠️ available_modes not a list, using default")
            available_modes = ["default"]

        # Clean up the list
        available_modes = [str(mode).strip() for mode in available_modes if str(mode).strip()]

        if not available_modes:
            available_modes = ["default"]

        print(f"📋 Available modes: {available_modes}")
        return available_modes

    def _create_mode_instance(self, mode_name):
        """Create an instance of the specified mode class"""
        if mode_name == "default":
            # Use BaseMode directly for default behavior
            return BaseMode()

        try:
            module_name = f"{mode_name}_mode"
            print(f"🔍 Trying to import: modes.{module_name}")

            # Try to import the mode module with _mode suffix
            exec(f"import modes.{module_name} as mode_module")
            mode_module = locals()['mode_module']

            # Look for a class that inherits from BaseMode
            for attr_name in dir(mode_module):
                attr = getattr(mode_module, attr_name)
                if (hasattr(attr, '__bases__') and
                        any('BaseMode' in str(base) for base in attr.__bases__)):
                    print(f"🏗️ Found mode class: {attr_name}")
                    return attr()

            raise Exception(f"No BaseMode-derived class found in mode {module_name}")

        except ImportError as e:
            print(f"❌ Cannot import mode {mode_name} (tried modes.{module_name}): {e}")

            # Try without _mode suffix as fallback
            try:
                print(f"🔍 Fallback: Trying to import: modes.{mode_name}")
                exec(f"import modes.{mode_name} as mode_module")
                mode_module = locals()['mode_module']

                # Look for a class that inherits from BaseMode
                for attr_name in dir(mode_module):
                    attr = getattr(mode_module, attr_name)
                    if (hasattr(attr, '__bases__') and
                            any('BaseMode' in str(base) for base in attr.__bases__)):
                        print(f"🏗️ Found mode class: {attr_name}")
                        return attr()

                raise Exception(f"No BaseMode-derived class found in mode {mode_name}")

            except ImportError as e2:
                print(f"❌ Fallback also failed: {e2}")
                if mode_name != "default":
                    print("🔄 Falling back to default BaseMode")
                    return BaseMode()
                else:
                    raise Exception("Cannot create default mode")
        except Exception as e:
            print(f"❌ Error creating mode {mode_name}: {e}")
            if mode_name != "default":
                print("🔄 Falling back to default BaseMode")
                return BaseMode()
            else:
                raise

    def load_mode(self, mode_name):
        """Load and initialize a mode"""
        print(f"📦 Loading mode: {mode_name}")

        try:
            # Clean up current mode
            if self.current_mode_instance:
                try:
                    self.current_mode_instance.cleanup(self.crow, self.config)
                except Exception as e:
                    print(f"⚠️ Cleanup error: {e}")

            # Create new mode instance
            self.current_mode_instance = self._create_mode_instance(mode_name)
            self.current_mode_name = mode_name

            print(f"✅ Mode loaded: {mode_name}")

            # Flash LEDs to indicate mode
            try:
                mode_position = self.available_modes.index(mode_name) + 1
                self.crow.leds.flash_eyes(times=mode_position)
            except:
                self.crow.leds.flash_eyes(times=1)

            return True

        except Exception as e:
            print(f"❌ Failed to load mode {mode_name}: {e}")
            # Try to fall back to default
            if mode_name != "default":
                print("🔄 Falling back to default mode")
                self.current_mode_instance = BaseMode()
                self.current_mode_name = "default"
                return True
            else:
                raise Exception(f"Cannot load any mode: {e}")

    def cycle_mode(self):
        """Switch to the next available mode"""
        try:
            current_index = self.available_modes.index(self.current_mode_name)
        except ValueError:
            current_index = 0

        next_index = (current_index + 1) % len(self.available_modes)
        next_mode = self.available_modes[next_index]

        print(f"🔄 Mode switching: {self.current_mode_name} → {next_mode}")

        self.load_mode(next_mode)

    def run_current_mode(self):
        """Run the current mode"""
        if self.current_mode_instance:
            print(f"🚀 Running mode: {self.current_mode_name}")
            self.current_mode_instance.run(self.crow, self.config)
        else:
            raise Exception("No mode instance available")

    def get_mode_info(self):
        """Get information about current mode"""
        return {
            "current_mode": self.current_mode_name,
            "available_modes": self.available_modes,
            "current_position": self.available_modes.index(
                self.current_mode_name) + 1 if self.current_mode_name in self.available_modes else 0,
            "total_modes": len(self.available_modes),
            "mode_class": type(self.current_mode_instance).__name__ if self.current_mode_instance else "Unknown"
        }