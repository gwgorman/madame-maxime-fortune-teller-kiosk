import unittest

from lightelf_adapter import (
    FRONT_SCENES,
    LightElfController,
    SimulatedLightElfTransport,
)


class LightElfControllerTests(unittest.TestCase):
    def setUp(self):
        self.transport = SimulatedLightElfTransport()
        self.controller = LightElfController(self.transport)

    def test_output_is_rejected_until_armed(self):
        with self.assertRaises(RuntimeError):
            self.controller.show("big_top", now=10.0)
        self.assertEqual(self.transport.operations, [("blackout",)])

    def test_every_front_scene_renders_in_simulation(self):
        for name in FRONT_SCENES:
            self.controller.arm(now=10.0)
            self.controller.show(name, now=10.1)
            self.controller.blackout()
        self.assertEqual(
            sum(operation[0] in {"text", "svg"} for operation in self.transport.operations),
            len(FRONT_SCENES),
        )

    def test_expired_lease_forces_blackout(self):
        self.controller.arm(now=10.0, ttl=0.5)
        self.controller.show("circus_star", now=10.1)
        self.assertTrue(self.controller.tick(now=10.5))
        self.assertFalse(self.controller.armed)
        self.assertEqual(self.transport.operations[-1], ("blackout",))

    def test_heartbeat_extends_lease(self):
        self.controller.arm(now=10.0, ttl=0.5)
        self.controller.heartbeat(now=10.4, ttl=0.5)
        self.assertFalse(self.controller.tick(now=10.89))
        self.assertTrue(self.controller.tick(now=10.9))

    def test_party_title_has_ascii_projector_fallback(self):
        self.assertEqual(FRONT_SCENES["party_title"].content, "CIRQUE DU SOIREE")


if __name__ == "__main__":
    unittest.main()
