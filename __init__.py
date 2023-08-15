from st3m.goose import List
from st3m.input import InputState
from st3m.application import Application, ApplicationContext
from ctx import Context
import captouch
import bl00mbox
import leds

blm = bl00mbox.Channel("Scalar")

class Scale:
    __slots__ = ("name", "notes")
    name: str
    notes: List[int]

    def __init__(self, name: str, notes: List[int]):
        self.name = name
        self.notes = notes

    def note(self, i: int) -> int:
        octave, note = divmod(i, len(self.notes))
        return self.notes[note] + octave * 12

scales = [
    Scale("Major", [0, 2, 4, 5, 7, 9, 11]),
    Scale("Natural Minor", [0, 2, 3, 5, 7, 8, 10]),
    Scale("Harmonic Minor", [0, 2, 3, 5, 7, 8, 11]),
    Scale("Major Pentatonic", [0, 2, 4, 7, 9]),
    Scale("Minor Pentatonic", [0, 3, 5, 7, 10]),
    Scale("Diminished", [0, 2, 3, 5, 6, 8, 9, 11]),
    Scale("Augmented", [0, 3, 4, 7, 8, 11]),
    Scale("Whole Tone", [0, 2, 4, 6, 8, 10]),
]

note_names = [
    "A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"
]

class ScalarApp(Application):
    def __init__(self, app_ctx: ApplicationContext) -> None:
        super().__init__(app_ctx)

        self.color_intensity = 0.0
        self.scale_base = 0
        self.scale_index = 0
        self.scale: Scale = scales[0]
        self.synths = [blm.new(bl00mbox.patches.tinysynth) for i in range(10)]
        self.cp_prev = captouch.read()

        for synth in self.synths:
            synth.signals.decay = 500
            synth.signals.waveform = 0
            synth.signals.attack = 50
            synth.signals.volume = 0.3 * 32767
            synth.signals.sustain = 0.9 * 32767
            synth.signals.release = 800
            synth.signals.output = blm.mixer

        self._update_leds()

    def _update_leds(self) -> None:
        hue = 30 * (self.scale_base % 12) + (30 / len(scales)) * self.scale_index
        leds.set_all_hsv(hue, 1, 0.2)
        leds.update()

    def _set_base(self, i: int) -> None:
        if i != self.scale_base:
            self.scale_base = i
            self._update_leds()

    def _set_scale(self, i: int) -> None:
        i = i % len(scales)
        if i != self.scale_index:
            self.scale_index = i
            self.scale = scales[i]
            self._update_leds()

    def _base_note_name(self) -> str:
        return note_names[self.scale_base % 12]

    def draw(self, ctx: Context) -> None:
        ctx.rgb(0, 0, 0).rectangle(-120, -120, 240, 240).fill()

        ctx.rgb(255, 255, 255)
        ctx.text_align = ctx.CENTER
        ctx.text_baseline = ctx.MIDDLE

        ctx.move_to(0, -10)
        ctx.text(self._base_note_name())
        ctx.move_to(0, 10)
        ctx.text(self.scale.name)

    def think(self, ins: InputState, delta_ms: int) -> None:
        super().think(ins, delta_ms)

        if self.color_intensity > 0:
            self.color_intensity -= self.color_intensity / 20

        if self.input.buttons.app.left.pressed:
            self._set_base(self.scale_base - 1)
        if self.input.buttons.app.right.pressed:
            self._set_base(self.scale_base + 1)
        if self.input.buttons.app.middle.pressed:
            self._set_scale(self.scale_index + 1)

        cts = captouch.read()
        for i in range(10):
            if cts.petals[i].pressed and (not self.cp_prev.petals[i].pressed):
                self.synths[i].signals.pitch.tone = self.scale_base + self.scale.note(i)
                self.synths[i].signals.trigger.start()
                self.color_intensity = 1.0
            elif (not cts.petals[i].pressed) and self.cp_prev.petals[i].pressed:
                self.synths[i].signals.trigger.stop()

        self.cp_prev = cts
