from HersheyFonts import HersheyFonts as _HersheyFonts

class gcodeWriter:
    def __init__(self, UP_Z, DOWN_Z, TRAVEL, CUT_SPEED, CLOSE_THRESH):
        self.UP_Z = UP_Z
        self.DOWN_Z = DOWN_Z
        self.TRAVEL = TRAVEL
        self.CUT_SPEED = CUT_SPEED
        self.CLOSE_THRESH = CLOSE_THRESH

        self.font = _HersheyFonts()
        self.font.load_default_font()

    def _find_maximum_font_size(self, text):
        size = 1
        for i in range(1, 12):
            x_max = 0
            y_max = 0

            self.font.normalize_rendering(i)
            for (x1, y1), (x2, y2) in self.font.lines_for_text(text):
                if x1 > x_max:
                    x_max = x1
                if x2 > x_max:
                    x_max = x2

                if y1 > y_max:
                    y_max = y1
                if y2 > y_max:
                    y_max = y2

            if x_max > 36 or y_max > 23:
                return size
            
            size = i

        return size


    def _get_centering_offsets(self, text, size):
        x_max = 0
        y_max = 0

        self.font.normalize_rendering(size)
        for (x1, y1), (x2, y2) in self.font.lines_for_text(text):
            if x1 > x_max:
                x_max = x1
            if x2 > x_max:
                x_max = x2

            if y1 > y_max:
                y_max = y1
            if y2 > y_max:
                y_max = y2

        x_offset = 60 - (x_max / 2)
        y_offset = 66 - (y_max / 2)

        return x_offset, y_offset
    
    def write_gcode(self, text):
        size = self._find_maximum_font_size(text)

        x_offset, y_offset = self._get_centering_offsets(text, size)

        output = ""
        output += f"LOCK\n"
        last_command = (-1000, -1000)
        is_down = False

        self.font.normalize_rendering(size)
        for (x1, y1), (x2, y2) in self.font.lines_for_text(text):
            x1 += x_offset
            x2 += x_offset
            y1 += y_offset
            y2 += y_offset

            x_close = abs(last_command[0] - x1) < self.CLOSE_THRESH
            y_close = abs(last_command[1] - y1) < self.CLOSE_THRESH
            start_is_close = x_close and y_close

            if not start_is_close:
                if is_down:
                    output += f"G1 Z{self.UP_Z} F{self.TRAVEL}\n"
                    is_down = False
                output += f"G1 X{x1} Y{y1} F{self.TRAVEL}\n"

            if (not is_down):
                output += f"G1 Z{self.DOWN_Z} F{self.CUT_SPEED}\n"
                is_down = True

            output += f"G1 X{x2} Y{y2} F{self.CUT_SPEED}\n" # move to point 2
            
            last_command = (x2, y2)

        output += f"UNLOCK\n"
        output += f"G1 Z120 F{self.TRAVEL}\n"

        return output