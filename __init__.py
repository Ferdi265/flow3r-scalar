from st3m.ui.view import ViewManager
from st3m.goose import Optional, List, Enum
from st3m.input import InputState
from st3m.application import Application, ApplicationContext
from ctx import Context
import captouch
import bl00mbox
import errno
import leds
import math
import time
import json
import os

blm = bl00mbox.Channel("Scalar")

class Scale:
    __slots__ = ("name", "notes")
    name: str
    notes: List[int]

    def __init__(self, name: str, notes: List[int]):
        self.name = name
        self.notes = notes

    def note(self, i: int, mode: int) -> int:
        octave, note = divmod(i + mode , len(self.notes))
        return self.notes[note] - self.notes[mode] + octave * 12

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

        try:
            self.bundle_path = app_ctx.bundle_path
        except Exception:
            self.bundle_path = "/flash/sys/apps/yrlf-flow3r-scalar"

        self._load_settings()

        self._ui_state = UI_PLAY
        self._ui_mid_prev_time = 0
        self._ui_cap_prev = captouch.read()
        self._color_intensity = 0.0
        self._scale_key = 0
        self._scale_offset = 0
        self._scale_mode = 0
        self._scale_index = 0
        self._scale: Scale = self._scales[0]
        self._synths = [blm.new(bl00mbox.patches.tinysynth) for i in range(10)]

        for synth in self._synths:
            synth.signals.decay = 500
            synth.signals.waveform = 0
            synth.signals.attack = 50
            synth.signals.volume = 0.3 * 32767
            synth.signals.sustain = 0.6 * 32767
            synth.signals.release = 800
            synth.signals.output = blm.mixer

        self._update_leds()

    def _load_settings(self) -> None:
        settings = self._try_load_settings(self.bundle_path + "/scalar-default.json")
        assert settings is not None, "failed to load default settings"

        user_settings = self._try_load_settings("/flash/scalar.json")
        if user_settings is not None:
            settings.update(user_settings)

        if settings != user_settings:
            self._try_write_settings("/flash/scalar.json", settings)

        self._scales = [ Scale(scale["name"], scale["notes"]) for scale in settings["scales"] ]
        self._ui_labels = settings["ui_labels"]

    def _try_load_settings(self, path: str) -> Optional[dict]:
        try:
            with open(path, "r") as f:
                return json.load(f)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise # ignore file not found

    def _try_write_settings(self, path: str, settings: dict) -> None:
        with open(path, "w") as f:
            json.dump(settings, f)

    def _update_leds(self) -> None:
        hue = 30 * (self._scale_key % 12) + (30 / len(self._scales)) * self._scale_index
        leds.set_all_hsv(hue, 1, 0.2)
        leds.update()

    def _set_key(self, i: int) -> None:
        if i != self._scale_key:
            self._scale_key = i
            self._update_leds()

    def _set_scale(self, i: int) -> None:
        i = i % len(self._scales)
        if i != self._scale_index:
            self._scale_index = i
            self._scale = self._scales[i]
            self._scale_mode %= len(self._scale.notes)
            self._scale_offset %= len(self._scale.notes)
            self._update_leds()

    def _set_mode(self, i: int) -> None:
        i = i % len(self._scale.notes)
        self._scale_mode = i

    def _set_offset(self, i: int) -> None:
        i = i % len(self._scale.notes)
        self._scale_offset = i

    def _key_name(self) -> str:
        return note_names[self._scale_key % 12]

    def on_enter(self, vm: Optional[ViewManager]) -> None:
        super().on_enter(vm)
        self._load_settings()

    def on_exit(self) -> None:
        for synth in self._synths:
            synth.signals.trigger.stop()

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

        while ctx.text_width(self._scale.name) > 200:
            ctx.font_size -= 1
        ctx.rgb(255, 255, 255)
        ctx.move_to(0, 12)
        ctx.text(self._scale.name)

        def draw_text(petal, r, text, inv = False):
            ctx.save()
            if inv:
                petal = (petal + 5) % 10
                r = -r
            ctx.rotate(petal * math.tau / 10 + math.pi)
            ctx.move_to(0, r)
            ctx.text(text)
            ctx.restore()

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

        ctx.font_size = 14
        if self._ui_state == UI_KEY or self._ui_state == UI_SELECT:
            draw_dot(8, 90)
            if self._ui_labels:
                draw_text(8, 75, "KEY", inv=True)
        if self._ui_state == UI_SCALE or self._ui_state == UI_SELECT:
            draw_dot(2, 90)
            if self._ui_labels:
                draw_text(2, 75, "SCALE", inv=True)
        if self._ui_state == UI_MODE or self._ui_state == UI_SELECT:
            draw_dot(6, 90)
            if self._ui_labels:
                draw_text(6, 75, "MODE")
        if self._ui_state == UI_OFFSET or self._ui_state == UI_SELECT:
            draw_dot(4, 90)
            if self._ui_labels:
                draw_text(4, 75, "OFFSET")
        if self._ui_state == UI_SELECT:
            draw_dot(0, 90)
            if self._ui_labels:
                draw_text(0, 75, "PLAY", inv=True)

        draw_tri(self._scale_offset, 110)
        if self._scale_mode != 0:
            orig_root_scale_degree = len(self._scale.notes) - self._scale_mode
            orig_root_petal = (orig_root_scale_degree + self._scale_offset) % len(self._scale.notes)
            draw_line(orig_root_petal, 110)

    def think(self, ins: InputState, delta_ms: int) -> None:
        super().think(ins, delta_ms)

        if self._color_intensity > 0:
            self._color_intensity -= self._color_intensity / 20

        if self.input.buttons.app.middle.pressed:
            mid_time = time.ticks_ms()
            if self._ui_state == UI_SELECT:
                self._ui_state = UI_PLAY
            if self._ui_state != UI_PLAY or mid_time - self._ui_mid_prev_time < DOUBLE_TAP_THRESH_MS:
                self._ui_state = UI_SELECT
            self._ui_mid_prev_time = mid_time

        if self._ui_state == UI_PLAY:
            if self.input.buttons.app.left.pressed:
                self._set_key(self._scale_key - 12)
            if self.input.buttons.app.right.pressed:
                self._set_key(self._scale_key + 12)
        elif self._ui_state == UI_KEY:
            if self.input.buttons.app.left.pressed:
                self._set_key(self._scale_key - 1)
            if self.input.buttons.app.right.pressed:
                self._set_key(self._scale_key + 1)
        elif self._ui_state == UI_SCALE:
            if self.input.buttons.app.left.pressed:
                self._set_scale(self._scale_index - 1)
            if self.input.buttons.app.right.pressed:
                self._set_scale(self._scale_index + 1)
        elif self._ui_state == UI_MODE:
            if self.input.buttons.app.left.pressed:
                self._set_mode(self._scale_mode - 1)
            if self.input.buttons.app.right.pressed:
                self._set_mode(self._scale_mode + 1)
        elif self._ui_state == UI_OFFSET:
            if self.input.buttons.app.left.pressed:
                self._set_offset(self._scale_offset - 1)
            if self.input.buttons.app.right.pressed:
                self._set_offset(self._scale_offset + 1)

        cts = captouch.read()
        for i in range(10):
            pressed = cts.petals[i].pressed and not self._ui_cap_prev.petals[i].pressed
            released = not cts.petals[i].pressed and self._ui_cap_prev.petals[i].pressed
            if self._ui_state == UI_SELECT:
                if pressed:
                    if i == 0:
                        self._ui_state = UI_PLAY
                    elif i == 8:
                        self._ui_state = UI_KEY
                    elif i == 2:
                        self._ui_state = UI_SCALE
                    elif i == 6:
                        self._ui_state = UI_MODE
                    elif i == 4:
                        self._ui_state = UI_OFFSET
            else:
                half_step_up = int(self.input.buttons.app.middle.down)
                if pressed:
                    self._synths[i].signals.pitch.tone = (
                        self._scale_key +
                        self._scale.note(i - self._scale_offset, self._scale_mode) +
                        half_step_up
                    )
                    self._synths[i].signals.trigger.start()
                    self._color_intensity = 1.0
                elif released:
                    self._synths[i].signals.trigger.stop()
        self._ui_cap_prev = cts
