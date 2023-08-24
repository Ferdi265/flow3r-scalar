# Scalar

A better melodic instrument application for the
[flow3r](https://flow3r.garden) that supports many different musical scales.

## Scales

- Major scale
- Natural Minor scale
- Harmonic Minor scale
- Major Pentatonic scale
- Minor Pentatonic scale
- Blues scale
- Diminished scale
- Augmented scale
- Whole Tone scale

The Natural Minor scale and the Minor Pentatonic scale are Modes of the
respective Major scale and can also be played with the *Mode* setting, but are
included separately for simplicity since they are often used.

## Controls

The capacitive petals can be used to play notes from the current scale in
clockwise order starting from the top petal (marked with ▲).

The app has a few different interactive menus to allow changing parameters such
as the Octave, Key, Scale, Mode, or Offset live while still being able to play
notes for quick feedback. The menus only differ in the behaviour of the app
shoulder button (the left shoulder button by default), with the exception of
the settings menu.

### Play Mode

This is the default mode.

- tilt left: decrease octave
- tilt right: increase octave
- press down: raise all played notes by a half step while held down
- double tap down: go to Settings Menu

## Settings Menu

Select which parameter to change. This menu is indicated by five squares (◼)
next to the five pink petals. In this menu you cannot play notes with the
capacitive petals.

- press down: go to Play Mode
- top petal: go to Play Mode
- left petal: go to Key Menu
- right petal: go to Scale Menu
- bottom left petal: go to Mode Menu
- bottom right petal: go to Offset Menu

## Key Menu

Select which Key to play. Default is the key of A. The current key is always
displayed in the center of the screen.

This menu is indicated by a square (◼) next to the left petal.

- tilt left: decrease key by a half step
- tilt right: increase key by a half step
- press down: go to Settings Menu

## Scale Menu

Select which Scale to play. Default is the Major scale. The current scale is
always displayed in the center of the screen.

This menu is indicated by a square (◼) next to the right petal.

- tilt left: previous scale
- tilt right: next scale
- press down: go to Settings Menu

## Mode Menu

Select which Mode of the current scale to play. A mode is formed by starting
the interval sequence of the current scale from a different point. The current
mode is indicated by a line (|) at the note where the interval sequence wraps
around.

This menu is indicated by a square (◼) next to the bottom left petal.

- tilt left: previous mode
- tilt right: next mode
- press down: go to Settings Menu

## Offset Menu

Select at which petal the root note of the current scale should be located. The
petal that will play the root of the current scale is marked with a triangle
(▲).

This menu is indicated by a square (◼) next to the bottom right petal.

- tilt left: increase offset
- tilt right: decrease offset
- press down: go to Settings Menu

## Installation

Put all files from this repo into `/sys/apps/yrlf-flow3r-scalar/` on your
flow3r's flash.

After first launch, you can edit the settings file in `scalar.json` on your
flow3r's flash.
