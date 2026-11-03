#!/usr/bin/env python3
"""Silent simulated Madame Maxime touchscreen kiosk."""

from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from fortune_engine import TOPICS
from lighting import LightingController
from session import EventJournal, SessionController, SessionState, default_journal_path
from voice_input import VoiceChoiceAdapter


WIDTH, HEIGHT = 1920, 1080
GOLD = (224, 176, 74)
PALE_GOLD = (255, 225, 151)
BURGUNDY = (67, 9, 28)
DEEP_RED = (34, 4, 18)
INK = (13, 8, 19)
TEAL = (44, 174, 165)
CREAM = (246, 229, 188)
MUTED = (169, 137, 110)
QUESTION_ACCENTS = (GOLD, TEAL, (177, 112, 214), (232, 116, 72))
OFFICE_CONFIG_PATH = Path.home() / ".config" / "startrek-console.json"
OFFICE_SERVICE = "app-startrek@autostart.service"


def prepare_office_preferences(config_path: Path = OFFICE_CONFIG_PATH) -> None:
    """Select a deterministic Office Mode landing page without losing settings."""
    try:
        preferences = json.loads(config_path.read_text(encoding="utf-8"))
        if not isinstance(preferences, dict):
            preferences = {}
    except (FileNotFoundError, OSError, ValueError, TypeError):
        preferences = {}
    preferences.update({
        "display_mode": "SHIP STATUS",
        "status_page": "NETWORK",
        "venue_override": "OFFICE",
    })
    config_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix="startrek-console-", suffix=".json", dir=config_path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(preferences, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, config_path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def launch_office_console(config_path: Path = OFFICE_CONFIG_PATH, runner=subprocess.run) -> None:
    prepare_office_preferences(config_path)
    runner(["systemctl", "--user", "start", OFFICE_SERVICE], check=True)


class SilentKiosk:
    def __init__(self, pygame, fullscreen: bool, enable_dmx: bool = False,
                 enable_voice: bool = True) -> None:
        self.pg = pygame
        flags = pygame.FULLSCREEN if fullscreen else pygame.RESIZABLE
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
        pygame.display.set_caption("Madame Maxime — Silent Simulator")
        self.clock = pygame.time.Clock()
        self.controller = SessionController(EventJournal(default_journal_path()))
        self.started = time.monotonic()
        self.notice = "SILENT DEVELOPMENT MODE — AUDIO DISABLED"
        self.notice_until = float("inf")
        self.running = True
        self.operator_menu_open = False
        self.next_action = None
        self.scale = 1.0
        self.offset = (0, 0)
        self.fonts = {}
        self.portrait = self.load_portrait()
        self.portrait_scaled = None
        self.portrait_scaled_size = None
        self.lighting = LightingController(enable_dmx)
        self.voice = VoiceChoiceAdapter() if enable_voice else None
        self.voice_prompt_key = None
        self.voice_state = "off" if not enable_voice else "waiting"
        self.voice_selection = None
        self.voice_apply_at = None
        self.transition_selection = None
        self.transition_until = 0.0
        self.lighting.start()
        if enable_dmx and not self.lighting.available:
            self.notice = "DMX OFFLINE — TOUCHSCREEN CONTINUES SAFELY"
            self.notice_until = time.monotonic() + 6.0

    def load_portrait(self):
        """Load Greg's approved Madame Maxime artwork without modifying it."""
        path = Path(__file__).resolve().parent / "assets" / "madame-maxime-at-the-crystal-ball.png"
        try:
            return self.pg.image.load(str(path)).convert()
        except (FileNotFoundError, self.pg.error):
            return None

    def font(self, size: int, bold: bool = False):
        key = (size, bold)
        if key not in self.fonts:
            preferred = "Copperplate" if "Copperplate" in self.pg.font.get_fonts() else None
            self.fonts[key] = self.pg.font.SysFont(preferred, size, bold=bold)
        return self.fonts[key]

    def transform(self, x: float, y: float) -> tuple[int, int]:
        return int(self.offset[0] + x * self.scale), int(self.offset[1] + y * self.scale)

    def rect(self, x: float, y: float, w: float, h: float):
        px, py = self.transform(x, y)
        return self.pg.Rect(px, py, int(w * self.scale), int(h * self.scale))

    def draw_text(self, text, size, color, center, bold=False, max_width=None):
        font = self.font(max(12, int(size * self.scale)), bold)
        if max_width is None:
            surface = font.render(text, True, color)
            self.screen.blit(surface, surface.get_rect(center=self.transform(*center)))
            return
        words = text.split()
        lines, line = [], []
        limit = max_width * self.scale
        for word in words:
            trial = " ".join(line + [word])
            if line and font.size(trial)[0] > limit:
                lines.append(" ".join(line))
                line = [word]
            else:
                line.append(word)
        if line:
            lines.append(" ".join(line))
        line_height = font.get_linesize()
        start_y = self.transform(*center)[1] - (len(lines) * line_height) // 2
        for index, value in enumerate(lines):
            surface = font.render(value, True, color)
            self.screen.blit(surface, surface.get_rect(center=(self.transform(*center)[0], start_y + index * line_height)))

    def button(self, key, label, box, color=GOLD, text_color=INK):
        rect = self.rect(*box)
        self.pg.draw.rect(self.screen, (20, 11, 19), rect.inflate(10, 10), border_radius=int(24 * self.scale))
        self.pg.draw.rect(self.screen, color, rect, border_radius=int(20 * self.scale))
        self.pg.draw.rect(self.screen, PALE_GOLD, rect, width=max(2, int(3 * self.scale)), border_radius=int(20 * self.scale))
        self.draw_text(label, 31, text_color, (box[0] + box[2] / 2, box[1] + box[3] / 2), True)
        return key, rect

    def choice_buttons(self, prefix, values, x=1325, y=285, width=500, height=104,
                       gap=26, selected=None, base_color=(191, 137, 55)):
        buttons = []
        columns = 2 if len(values) > 3 else 1
        cell_width = (width - gap) / 2 if columns == 2 else width
        for index, value in enumerate(values):
            row, column = divmod(index, columns)
            box = (x + column * (cell_width + gap), y + row * (height + gap), cell_width, height)
            color = TEAL if value == selected else base_color
            buttons.append(self.button(f"{prefix}:{value}", value, box, color, INK))
        return buttons

    def voice_prompt(self):
        state = self.controller.state
        if state is SessionState.QUESTIONNAIRE:
            key, prompt, choices = self.controller.current_question
            return (state.value, self.controller.question_index, key), prompt, choices
        if state is SessionState.TOPIC:
            return (state.value,), "What shall I examine?", TOPICS
        if state is SessionState.RETURN_PROMPT:
            choices = ("YES", "NOT YET", "IT GOT WORSE")
            return (state.value,), "Has the previous fortune already come true?", choices
        return None

    def apply_voice_selection(self, selected, now):
        state = self.controller.state
        if state is SessionState.QUESTIONNAIRE:
            accepted = self.controller.select_answer(selected, now)
        if state is SessionState.TOPIC:
            accepted = self.controller.select_topic(selected, now)
        elif state is SessionState.RETURN_PROMPT:
            accepted = self.controller.answer_return(selected, now)
        elif state is not SessionState.QUESTIONNAIRE:
            accepted = False
        if accepted:
            self.begin_transition(selected, now)
        return accepted

    def begin_transition(self, selected, now):
        self.transition_selection = selected
        # Long enough to register through party noise, conversation, and drinks.
        self.transition_until = now + 2.0

    def transition_active(self, now):
        if self.transition_selection and now < self.transition_until:
            return True
        if self.transition_selection:
            self.transition_selection = None
        return False

    def sync_voice(self, now):
        if not self.voice:
            return
        prompt = self.voice_prompt()
        key = prompt[0] if prompt else None
        if key != self.voice_prompt_key:
            self.voice.invalidate()
            self.voice_prompt_key = key
            self.voice_selection = None
            self.voice_apply_at = None
            self.voice_state = "waiting" if prompt else "off"

        for kind, payload in self.voice.poll():
            if kind == "thinking":
                self.voice_state = "thinking"
            elif kind == "result":
                selected = payload.get("selected")
                if selected:
                    self.voice_selection = selected
                    self.voice_apply_at = now + 1.8
                    self.voice_state = "confirmed"
                else:
                    self.voice_state = "fallback"
            elif kind == "error":
                self.voice_state = "fallback"

        if self.voice_selection and self.voice_apply_at and now >= self.voice_apply_at:
            selected = self.voice_selection
            self.voice.invalidate()
            self.voice_selection = None
            self.voice_apply_at = None
            if self.apply_voice_selection(selected, now):
                self.voice_state = "waiting"
            return

        if self.transition_active(now):
            return

        if prompt and self.voice_state == "waiting" and not self.voice.busy:
            _key, spoken_prompt, choices = prompt
            if self.voice.start(spoken_prompt, choices):
                self.voice_state = "listening"

    def voice_status_copy(self):
        if self.voice_state == "listening":
            return "LISTENING — SAY ONE CHOICE", TEAL
        if self.voice_state == "thinking":
            return "INTERPRETING…", PALE_GOLD
        if self.voice_state == "confirmed" and self.voice_selection:
            return f"HEARD: {self.voice_selection} — TAP TO CORRECT", TEAL
        if self.voice_state == "fallback":
            return "VOICE UNCLEAR — PLEASE TAP", (255, 115, 105)
        return "", MUTED

    def draw_frame(self, now):
        sw, sh = self.screen.get_size()
        self.scale = min(sw / WIDTH, sh / HEIGHT)
        self.offset = ((sw - WIDTH * self.scale) / 2, (sh - HEIGHT * self.scale) / 2)
        self.screen.fill(INK)
        panel = self.rect(24, 20, 1872, 1040)
        self.pg.draw.rect(self.screen, BURGUNDY, panel, border_radius=int(42 * self.scale))
        self.pg.draw.rect(self.screen, GOLD, panel, width=max(3, int(7 * self.scale)), border_radius=int(42 * self.scale))

        for index in range(31):
            x = 62 + index * 60
            pulse = 0.72 + 0.28 * math.sin(now * 1.4 + index * 0.42)
            color = tuple(int(component * pulse) for component in PALE_GOLD)
            self.pg.draw.circle(self.screen, color, self.transform(x, 54), max(3, int(8 * self.scale)))
            self.pg.draw.circle(self.screen, color, self.transform(x, 1025), max(3, int(8 * self.scale)))

        self.pg.draw.polygon(self.screen, DEEP_RED, [self.transform(30, 25), self.transform(395, 25), self.transform(280, 1055), self.transform(30, 1055)])
        self.pg.draw.polygon(self.screen, DEEP_RED, [self.transform(1890, 25), self.transform(1525, 25), self.transform(1640, 1055), self.transform(1890, 1055)])
        self.draw_text("MADAME MAXIME", 72, PALE_GOLD, (960, 102), True)
        self.draw_text("FORTUNES • REVELATIONS • EXCELLENT ADVICE", 24, MUTED, (960, 164), True)

        # The supplied portrait is the stage, rather than a decorative prop.
        # Letterboxing preserves the complete, approved artwork unchanged.
        stage = self.rect(650, 190, 620, 625)
        self.pg.draw.rect(self.screen, (9, 5, 10), stage.inflate(24, 24), border_radius=int(22 * self.scale))
        if self.portrait:
            source_w, source_h = self.portrait.get_size()
            fit = min(stage.width / source_w, stage.height / source_h)
            image_size = (max(1, int(source_w * fit)), max(1, int(source_h * fit)))
            if image_size != self.portrait_scaled_size:
                self.portrait_scaled = self.pg.transform.smoothscale(self.portrait, image_size)
                self.portrait_scaled_size = image_size
            image_rect = self.portrait_scaled.get_rect(center=stage.center)
            self.screen.blit(self.portrait_scaled, image_rect)

        else:
            crystal_center = stage.center
            radius = int(190 * self.scale)
            self.pg.draw.circle(self.screen, (39, 22, 62), crystal_center, radius)
            self.pg.draw.circle(self.screen, TEAL, crystal_center, radius, width=max(3, int(7 * self.scale)))
            self.draw_text("PORTRAIT SIGNAL LOST", 28, CREAM, (960, 500), True)
        self.pg.draw.rect(self.screen, GOLD, stage, width=max(3, int(7 * self.scale)), border_radius=int(16 * self.scale))
        self.pg.draw.rect(self.screen, PALE_GOLD, stage.inflate(-18, -18), width=max(1, int(2 * self.scale)), border_radius=int(10 * self.scale))

    def state_copy(self):
        state = self.controller.state
        if state is SessionState.IDLE:
            return "THE VEIL IS QUIET", "Approach when you are ready to be seen."
        if state is SessionState.APPROACH:
            return "AH… A VISITOR", "Come closer. Madame Maxime is consulting the machinery."
        if state is SessionState.READY:
            return "SHALL WE BEGIN?", "One touch, and the future becomes needlessly specific."
        if state is SessionState.QUESTIONNAIRE:
            return self.controller.current_question[1], "Choose carefully. The crystal is judgmental but discreet."
        if state is SessionState.TOPIC:
            return "WHAT SHALL I EXAMINE?", "Speak one choice, or touch the shape of your question."
        if state is SessionState.RETURN_PROMPT:
            return "YOU AGAIN", "The crystal remembers. Has the previous fortune already come true?"
        if state is SessionState.THINKING:
            return "THE SYMBOLS ARE ALIGNING", "Please refrain from reorganizing destiny."
        if state is SessionState.FAREWELL:
            return "THE VEIL CLOSES", "Go carefully—and behave as though this was all your idea."
        return "YOUR FORTUNE", "The mechanism has reached a conclusion."

    def draw_content(self, now):
        if self.operator_menu_open:
            self.draw_operator_menu()
            return
        title, subtitle = self.state_copy()
        if self.controller.state is SessionState.QUESTIONNAIRE:
            question_number = self.controller.question_index + 1
            accent = QUESTION_ACCENTS[self.controller.question_index]
            self.draw_text(f"QUESTION {question_number} OF 4", 28, accent, (415, 235), True, 390)
        self.draw_text(title, 36, CREAM, (415, 325), True, 390)
        if self.controller.state is SessionState.REVEAL and self.controller.fortune:
            card, prediction, observation, instruction = self.controller.fortune.display_parts()
            self.draw_text(self.controller.fortune.opening, 22, CREAM, (415, 505), False, 390)
            self.draw_text(card, 30, PALE_GOLD, (1500, 320), True, 400)
            self.draw_text(prediction, 22, CREAM, (1500, 430), False, 390)
            self.draw_text(observation, 20, PALE_GOLD, (1500, 565), False, 390)
            self.draw_text(instruction, 21, TEAL, (1500, 690), True, 390)
        elif self.controller.state is SessionState.RETURN_PROMPT and self.controller.previous_fortune:
            previous = self.controller.previous_fortune
            self.draw_text(f"VISIT {previous.visit_number + 1}", 23, PALE_GOLD, (415, 420), True)
            self.draw_text(previous.prediction, 20, CREAM, (415, 555), False, 390)
        else:
            self.draw_text(subtitle, 23, CREAM, (415, 475), False, 390)

        buttons = []
        state = self.controller.state
        if state is SessionState.IDLE:
            buttons.append(self.button("approach", "SIMULATE APPROACH", (680, 840, 560, 112)))
            if self.controller.previous_fortune:
                buttons.append(self.button("return", "SIMULATE RETURN", (1325, 845, 420, 100), TEAL, INK))
        elif state is SessionState.READY:
            buttons.append(self.button("begin", "RECEIVE MY FORTUNE", (650, 825, 620, 130)))
        elif state is SessionState.QUESTIONNAIRE:
            _key, _prompt, values = self.controller.current_question
            accent = QUESTION_ACCENTS[self.controller.question_index]
            buttons.extend(self.choice_buttons(
                "answer", values, selected=self.voice_selection, base_color=accent,
            ))
            for index in range(4):
                if index < self.controller.question_index:
                    color, radius = PALE_GOLD, 8
                elif index == self.controller.question_index:
                    color, radius = accent, 15
                else:
                    color, radius = (91, 48, 63), 8
                self.pg.draw.circle(
                    self.screen, color, self.transform(1410 + index * 62, 780),
                    max(4, int(radius * self.scale)),
                )
        elif state is SessionState.TOPIC:
            buttons.extend(self.choice_buttons("topic", TOPICS, y=260, height=92,
                                               selected=self.voice_selection))
        elif state is SessionState.RETURN_PROMPT:
            buttons.extend(self.choice_buttons(
                "outcome", ("YES", "NOT YET", "IT GOT WORSE"), y=315,
                height=112, selected=self.voice_selection,
            ))
        elif state is SessionState.REVEAL:
            buttons.append(self.button("finished", "THE VEIL MAY CLOSE", (690, 850, 540, 96), TEAL))
        elif state is SessionState.FAREWELL:
            buttons.append(self.button("reset", "ANOTHER SEEKER", (735, 855, 450, 96)))

        buttons.append(self.button("cancel", "RESET", (75, 925, 225, 72), (122, 45, 54), CREAM))
        buttons.append(self.button("operator", "OPERATOR", (1620, 925, 225, 72), (49, 83, 83), CREAM))
        self.buttons = buttons

        voice_copy, voice_color = self.voice_status_copy()
        if voice_copy:
            self.draw_text(voice_copy, 20, voice_color, (1500, 820), True, 500)

        self.draw_text(self.notice, 18, PALE_GOLD, (960, 1019), True)

        if self.transition_active(now):
            self.draw_transition_confirmation()

    def draw_transition_confirmation(self):
        veil = self.pg.Surface(self.screen.get_size(), self.pg.SRCALPHA)
        veil.fill((7, 3, 10, 218))
        self.screen.blit(veil, (0, 0))
        panel = self.rect(510, 315, 900, 410)
        self.pg.draw.rect(self.screen, DEEP_RED, panel, border_radius=int(34 * self.scale))
        self.pg.draw.rect(self.screen, TEAL, panel, width=max(4, int(8 * self.scale)), border_radius=int(34 * self.scale))
        self.draw_text(f"{self.transition_selection} RECEIVED", 58, PALE_GOLD, (960, 440), True, 760)
        if self.controller.state is SessionState.QUESTIONNAIRE:
            next_copy = f"NOW — QUESTION {self.controller.question_index + 1} OF 4"
        elif self.controller.state is SessionState.TOPIC:
            next_copy = "THE FOUR SIGNS ARE SET"
        else:
            next_copy = "THE CRYSTAL IS CONTINUING"
        self.draw_text(next_copy, 30, CREAM, (960, 585), True, 760)
        self.draw_text("Your answer has been recorded.", 22, MUTED, (960, 650), False, 760)
        self.buttons = []

    def draw_operator_menu(self):
        veil = self.pg.Surface(self.screen.get_size(), self.pg.SRCALPHA)
        veil.fill((7, 3, 10, 210))
        self.screen.blit(veil, (0, 0))
        panel = self.rect(420, 225, 1080, 630)
        self.pg.draw.rect(self.screen, DEEP_RED, panel, border_radius=int(30 * self.scale))
        self.pg.draw.rect(self.screen, GOLD, panel, width=max(3, int(6 * self.scale)), border_radius=int(30 * self.scale))
        self.draw_text("OPERATOR CONTROL", 54, PALE_GOLD, (960, 330), True)
        self.draw_text(
            "Return to the unattended Office telemetry console? Madame Maxime will close and both PAR fixtures will black out.",
            25, CREAM, (960, 475), False, 820,
        )
        self.buttons = [
            self.button("office_console", "RETURN TO OFFICE CONSOLE", (560, 610, 800, 112), GOLD, INK),
            self.button("operator_cancel", "CANCEL — KEEP FORTUNE TELLER", (660, 755, 600, 76), (49, 83, 83), CREAM),
        ]

    def handle_click(self, position):
        for key, rect in self.buttons:
            if not rect.collidepoint(position):
                continue
            now = time.monotonic()
            if key == "approach":
                self.controller.approach(now)
            elif key == "return":
                self.controller.approach(now, returning=True)
            elif key == "begin":
                self.controller.begin(now)
            elif key.startswith("answer:"):
                if self.voice:
                    self.voice.invalidate()
                selected = key.split(":", 1)[1]
                if self.controller.select_answer(selected, now):
                    self.begin_transition(selected, now)
            elif key.startswith("topic:"):
                if self.voice:
                    self.voice.invalidate()
                selected = key.split(":", 1)[1]
                if self.controller.select_topic(selected, now):
                    self.begin_transition(selected, now)
            elif key.startswith("outcome:"):
                if self.voice:
                    self.voice.invalidate()
                selected = key.split(":", 1)[1]
                if self.controller.answer_return(selected, now):
                    self.begin_transition(selected, now)
            elif key == "finished":
                self.controller.finish_reveal(now)
            elif key == "reset":
                self.controller.cancel(now)
                self.controller.approach(now)
            elif key == "cancel":
                if self.voice:
                    self.voice.invalidate()
                self.controller.cancel(now)
            elif key == "operator":
                self.operator_menu_open = True
            elif key == "operator_cancel":
                self.operator_menu_open = False
            elif key == "office_console":
                self.next_action = "office"
                self.running = False
            break

    def run(self):
        while self.running:
            now = time.monotonic()
            self.controller.update(now)
            self.sync_voice(now)
            self.lighting.update(self.controller.state.value, now)
            for event in self.pg.event.get():
                if event.type == self.pg.QUIT:
                    self.running = False
                elif event.type == self.pg.KEYDOWN and event.key in (self.pg.K_ESCAPE, self.pg.K_q):
                    self.running = False
                elif event.type == self.pg.MOUSEBUTTONDOWN and event.button == 1:
                    self.handle_click(event.pos)
            if self.notice_until != float("inf") and now >= self.notice_until:
                self.notice = "SILENT DEVELOPMENT MODE — AUDIO DISABLED"
                self.notice_until = float("inf")
            self.draw_frame(now)
            self.draw_content(now)
            self.pg.display.flip()
            # Twelve frames per second is ample for lamps and touch feedback,
            # while leaving the Pi comfortable for future sensors and DMX.
            self.clock.tick(12)

def main() -> int:
    parser = argparse.ArgumentParser(description="Silent Madame Maxime kiosk simulator")
    parser.add_argument("--windowed", action="store_true", help="use a resizable window")
    parser.add_argument("--dmx", action="store_true", help="enable the verified ENTTEC Open DMX adapter")
    parser.add_argument("--no-voice", action="store_true", help="disable microphone choice input")
    args = parser.parse_args()
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    try:
        import pygame
    except ImportError:
        print("pygame is required: sudo apt install python3-pygame", file=sys.stderr)
        return 2
    # Audio is intentionally absent from this milestone. Do not call
    # pygame.init(), because that would also initialize the mixer device.
    pygame.display.init()
    pygame.font.init()
    kiosk = SilentKiosk(
        pygame, fullscreen=not args.windowed, enable_dmx=args.dmx,
        enable_voice=not args.no_voice,
    )
    try:
        kiosk.run()
    finally:
        # A DMX failure must never strand the kiosk or leave the PARs lit.
        kiosk.lighting.stop()
        pygame.font.quit()
        pygame.display.quit()
    if kiosk.next_action == "office":
        try:
            launch_office_console()
        except (OSError, subprocess.CalledProcessError) as exc:
            print(f"Unable to launch Office console: {exc}", file=sys.stderr)
            return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
