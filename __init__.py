from st3m.goose import Optional, List, Enum
from st3m.input import InputState
from st3m.application import Application, ApplicationContext
from ctx import Context
import captouch
import bl00mbox
import leds
import math
import time

blm = bl00mbox.Channel("Scalar")

class Scale:
    __slots__ = ("name", "notes")
    name: str
    notes: List[int]
    modes: Optional[List[str]]

    def __init__(self, name: str, notes: List[int], modes: Optional[List[str]] = None):
        self.name = name
        self.notes = notes
        self.modes = modes

    def note(self, i: int, mode: int) -> int:
        octave, note = divmod(i + mode , len(self.notes))
        return self.notes[note] - self.notes[mode] + octave * 12

scales = [
    Scale("Major", [0, 2, 4, 5, 7, 9, 11]),
    Scale("Natural Minor", [0, 2, 3, 5, 7, 8, 10]),
    Scale("Harmonic Minor", [0, 2, 3, 5, 7, 8, 11]),
    Scale("Major Pentatonic", [0, 2, 4, 7, 9]),
    Scale("Minor Pentatonic", [0, 3, 5, 7, 10]),
    Scale("Blues", [0, 3, 5, 6, 7, 10]),
    Scale("Diminished", [0, 2, 3, 5, 6, 8, 9, 11]),
    Scale("Augmented", [0, 3, 4, 7, 8, 11]),
    Scale("Whole Tone", [0, 2, 4, 6, 8, 10]),
]

note_names = [
    "A", "A# / Bb", "B", "C", "C# / Db", "D", "D# / Eb", "E", "F", "F# / Gb", "G", "G# / Ab"
]

UI_PLAY = 0
UI_KEY = 1
UI_SCALE = 2
UI_MODE = 3
UI_OFFSET = 4
UI_SELECT = 5
DOUBLE_TAP_THRESH_MS = 500

class ScalarApp(Application):
    def __init__(self, app_ctx: ApplicationContext) -> None:
        super().__init__(app_ctx)

        self.ui_state = UI_PLAY
        self.ui_mid_prev_time = 0
        self.ui_cap_prev = captouch.read()
        self.color_intensity = 0.0
        self.scale_key = 0
        self.scale_offset = 0
        self.scale_mode = 0
        self.scale_index = 0
        self.scale: Scale = scales[0]
        self.synths = [blm.new(bl00mbox.patches.tinysynth) for i in range(10)]

        for synth in self.synths:
            synth.signals.decay = 500
            synth.signals.waveform = 0
            synth.signals.attack = 50
            synth.signals.volume = 0.3 * 32767
            synth.signals.sustain = 0.6 * 32767
            synth.signals.release = 800
            synth.signals.output = blm.mixer

        self._update_leds()

    def _update_leds(self) -> None:
        hue = 30 * (self.scale_key % 12) + (30 / len(scales)) * self.scale_index
        leds.set_all_hsv(hue, 1, 0.2)
        leds.update()

    def _set_key(self, i: int) -> None:
        if i != self.scale_key:
            self.scale_key = i
            self._update_leds()

    def _set_scale(self, i: int) -> None:
        i = i % len(scales)
        if i != self.scale_index:
            self.scale_index = i
            self.scale = scales[i]
            self.scale_mode %= len(self.scale.notes)
            self.scale_offset %= len(self.scale.notes)
            self._update_leds()

    def _set_mode(self, i: int) -> None:
        i = i % len(self.scale.notes)
        self.scale_mode = i

    def _set_offset(self, i: int) -> None:
        i = i % len(self.scale.notes)
        self.scale_offset = i

    def _key_name(self) -> str:
        return note_names[self.scale_key % 12]

    def draw(self, ctx: Context) -> None:
        ctx.rgb(0, 0, 0)
        ctx.rectangle(-120, -120, 240, 240)
        ctx.fill()

        # center UI text
        ctx.text_align = ctx.CENTER
        ctx.text_baseline = ctx.MIDDLE
        ctx.font_size = 32
        ctx.rgb(255, 255, 255)
        ctx.move_to(0, -12)
        ctx.text(self._key_name())

        ctx.text_align = ctx.CENTER
        ctx.text_baseline = ctx.MIDDLE
        ctx.font_size = 32
        while ctx.text_width(self.scale.name) > 200:
            ctx.font_size -= 1
        ctx.rgb(255, 255, 255)
        ctx.move_to(0, 12)
        ctx.text(self.scale.name)

        def draw_dot(petal, r):
            ctx.save()
            ctx.rotate(petal * math.tau / 10 + math.pi)
            ctx.rectangle(-5, -5 + r, 10, 10).fill()
            ctx.restore()

        def draw_tri(petal, r):
            ctx.save()
            ctx.rotate(petal * math.tau / 10 + math.pi)
            ctx.move_to(-5, -5 + r)
            ctx.line_to(5, -5 + r)
            ctx.line_to(0, 5 + r)
            ctx.close_path()
            ctx.fill()
            ctx.restore()

        def draw_line(petal, r):
            ctx.save()
            ctx.rotate(petal * math.tau / 10 + math.pi)
            ctx.move_to(-1, -5 + r)
            ctx.line_to(1, -5 + r)
            ctx.line_to(1, 5 + r)
            ctx.line_to(-1, 5 + r)
            ctx.close_path()
            ctx.fill()
            ctx.restore()

        if self.ui_state == UI_KEY or self.ui_state == UI_SELECT:
            draw_dot(8, 90)
        if self.ui_state == UI_SCALE or self.ui_state == UI_SELECT:
            draw_dot(2, 90)
        if self.ui_state == UI_MODE or self.ui_state == UI_SELECT:
            draw_dot(6, 90)
        if self.ui_state == UI_OFFSET or self.ui_state == UI_SELECT:
            draw_dot(4, 90)
        if self.ui_state == UI_SELECT:
            draw_dot(0, 90)

        draw_tri(self.scale_offset, 110)
        if self.scale_mode != 0:
            orig_root_scale_degree = len(self.scale.notes) - self.scale_mode
            orig_root_petal = (orig_root_scale_degree + self.scale_offset) % len(self.scale.notes)
            draw_line(orig_root_petal, 110)

    def think(self, ins: InputState, delta_ms: int) -> None:
        super().think(ins, delta_ms)

        if self.color_intensity > 0:
            self.color_intensity -= self.color_intensity / 20

        if self.input.buttons.app.middle.pressed:
            mid_time = time.ticks_ms()
            if self.ui_state == UI_SELECT:
                self.ui_state = UI_PLAY
            if self.ui_state != UI_PLAY or mid_time - self.ui_mid_prev_time < DOUBLE_TAP_THRESH_MS:
                self.ui_state = UI_SELECT
            self.ui_mid_prev_time = mid_time

        if self.ui_state == UI_PLAY:
            if self.input.buttons.app.left.pressed:
                self._set_key(self.scale_key - 12)
            if self.input.buttons.app.right.pressed:
                self._set_key(self.scale_key + 12)
        elif self.ui_state == UI_KEY:
            if self.input.buttons.app.left.pressed:
                self._set_key(self.scale_key - 1)
            if self.input.buttons.app.right.pressed:
                self._set_key(self.scale_key + 1)
        elif self.ui_state == UI_SCALE:
            if self.input.buttons.app.left.pressed:
                self._set_scale(self.scale_index - 1)
            if self.input.buttons.app.right.pressed:
                self._set_scale(self.scale_index + 1)
        elif self.ui_state == UI_MODE:
            if self.input.buttons.app.left.pressed:
                self._set_mode(self.scale_mode - 1)
            if self.input.buttons.app.right.pressed:
                self._set_mode(self.scale_mode + 1)
        elif self.ui_state == UI_OFFSET:
            if self.input.buttons.app.left.pressed:
                self._set_offset(self.scale_offset - 1)
            if self.input.buttons.app.right.pressed:
                self._set_offset(self.scale_offset + 1)

        cts = captouch.read()
        for i in range(10):
            pressed = cts.petals[i].pressed and not self.ui_cap_prev.petals[i].pressed
            released = not cts.petals[i].pressed and self.ui_cap_prev.petals[i].pressed
            if self.ui_state == UI_SELECT:
                if pressed:
                    if i == 0:
                        self.ui_state = UI_PLAY
                    elif i == 8:
                        self.ui_state = UI_KEY
                    elif i == 2:
                        self.ui_state = UI_SCALE
                    elif i == 6:
                        self.ui_state = UI_MODE
                    elif i == 4:
                        self.ui_state = UI_OFFSET
            else:
                half_step_up = int(self.input.buttons.app.middle.down)
                if pressed:
                    self.synths[i].signals.pitch.tone = (
                        self.scale_key +
                        self.scale.note(i - self.scale_offset, self.scale_mode) +
                        half_step_up
                    )
                    self.synths[i].signals.trigger.start()
                    self.color_intensity = 1.0
                elif released:
                    self.synths[i].signals.trigger.stop()
        self.ui_cap_prev = cts
