#!/usr/bin/env python3
"""Silent simulated Madame Maxime touchscreen kiosk."""

from __future__ import annotations

import argparse
import math
import os
import sys
import time

from session import EventJournal, SessionController, SessionState, default_journal_path


WIDTH, HEIGHT = 1920, 1080
GOLD = (224, 176, 74)
PALE_GOLD = (255, 225, 151)
BURGUNDY = (67, 9, 28)
DEEP_RED = (34, 4, 18)
INK = (13, 8, 19)
TEAL = (44, 174, 165)
CREAM = (246, 229, 188)
MUTED = (169, 137, 110)


class SilentKiosk:
    def __init__(self, pygame, fullscreen: bool) -> None:
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
        self.scale = 1.0
        self.offset = (0, 0)
        self.fonts = {}

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

        crystal_center = self.transform(960, 465)
        radius = int(236 * self.scale)
        glow = 0.5 + 0.5 * math.sin(now * 0.9)
        self.pg.draw.circle(self.screen, (39, 22, 62), crystal_center, radius + int(28 * self.scale))
        self.pg.draw.circle(self.screen, (62, int(80 + glow * 45), 121), crystal_center, radius)
        self.pg.draw.circle(self.screen, TEAL, crystal_center, radius, width=max(3, int(7 * self.scale)))
        for ring in range(5):
            rr = int((75 + ring * 31 + 7 * math.sin(now + ring)) * self.scale)
            self.pg.draw.circle(self.screen, (83, 191, 181), crystal_center, rr, width=max(1, int(2 * self.scale)))
        self.pg.draw.ellipse(self.screen, (73, 42, 24), self.rect(710, 685, 500, 76))
        self.pg.draw.rect(self.screen, GOLD, self.rect(760, 720, 400, 88), border_radius=int(16 * self.scale))

    def state_copy(self):
        state = self.controller.state
        if state is SessionState.IDLE:
            return "THE VEIL IS QUIET", "Approach when you are ready to be seen."
        if state is SessionState.APPROACH:
            return "AH… A VISITOR", "Come closer. Madame Maxime is consulting the machinery."
        if state is SessionState.READY:
            return "SHALL WE BEGIN?", "One touch, and the future becomes needlessly specific."
        if state is SessionState.LISTENING:
            return "SPEAK YOUR QUESTION", "No microphone is active in this silent development build."
        if state is SessionState.THINKING:
            return "THE SYMBOLS ARE ALIGNING", "Please refrain from reorganizing destiny."
        if state is SessionState.FAREWELL:
            return "THE VEIL CLOSES", "Go carefully—and behave as though this was all your idea."
        return "YOUR FORTUNE", "The mechanism has reached a conclusion."

    def draw_content(self, now):
        title, subtitle = self.state_copy()
        self.draw_text(title, 42, CREAM, (960, 400), True, 650)
        if self.controller.state is SessionState.REVEAL and self.controller.fortune:
            card, prediction, observation, instruction = self.controller.fortune
            self.draw_text(card, 34, PALE_GOLD, (960, 462), True, 650)
            self.draw_text(prediction, 24, CREAM, (960, 532), False, 620)
            self.draw_text(observation, 21, PALE_GOLD, (960, 620), False, 620)
            self.draw_text(instruction, 22, TEAL, (960, 694), True, 620)
        else:
            self.draw_text(subtitle, 25, CREAM, (960, 538), False, 620)

        buttons = []
        state = self.controller.state
        if state is SessionState.IDLE:
            buttons.append(self.button("approach", "SIMULATE APPROACH", (680, 840, 560, 112)))
        elif state is SessionState.READY:
            buttons.append(self.button("begin", "RECEIVE MY FORTUNE", (650, 825, 620, 130)))
        elif state is SessionState.LISTENING:
            buttons.append(self.button("finished", "I HAVE SPOKEN", (690, 840, 540, 112), TEAL))
        elif state in (SessionState.REVEAL, SessionState.FAREWELL):
            buttons.append(self.button("reset", "ANOTHER SEEKER", (735, 855, 450, 96)))

        buttons.append(self.button("cancel", "RESET", (75, 925, 225, 72), (122, 45, 54), CREAM))
        buttons.append(self.button("operator", "OPERATOR", (1620, 925, 225, 72), (49, 83, 83), CREAM))
        self.buttons = buttons

        self.draw_text(self.notice, 18, PALE_GOLD, (960, 1019), True)

    def handle_click(self, position):
        for key, rect in self.buttons:
            if not rect.collidepoint(position):
                continue
            now = time.monotonic()
            if key == "approach":
                self.controller.approach(now)
            elif key == "begin":
                self.controller.begin(now)
            elif key == "finished":
                self.controller.guest_finished(now)
            elif key == "reset":
                self.controller.cancel(now)
                self.controller.approach(now)
            elif key == "cancel":
                self.controller.cancel(now)
            elif key == "operator":
                self.notice = "OPERATOR PANEL RESERVED — NO EXTERNAL SYSTEMS LAUNCHED"
                self.notice_until = now + 4.0
            break

    def run(self):
        while self.running:
            now = time.monotonic()
            self.controller.update(now)
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
            self.clock.tick(30)


def main() -> int:
    parser = argparse.ArgumentParser(description="Silent Madame Maxime kiosk simulator")
    parser.add_argument("--windowed", action="store_true", help="use a resizable window")
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
    try:
        SilentKiosk(pygame, fullscreen=not args.windowed).run()
    finally:
        pygame.font.quit()
        pygame.display.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
