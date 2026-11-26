"""The analyst limiter: per visitor, per instance, and the window slides."""

from app.ratelimit import SlidingWindow


def test_blocks_after_the_limit_and_says_when_to_retry():
    w = SlidingWindow(limit=2, window_s=60, instance_limit=100)
    assert w.check("a", now=0) == (True, 0)
    assert w.check("a", now=1) == (True, 0)
    allowed, retry = w.check("a", now=2)
    assert not allowed and 55 <= retry <= 60


def test_visitors_are_independent():
    w = SlidingWindow(limit=1, window_s=60, instance_limit=100)
    assert w.check("a", now=0)[0]
    assert not w.check("a", now=1)[0]
    assert w.check("b", now=1)[0]


def test_window_slides():
    w = SlidingWindow(limit=1, window_s=60, instance_limit=100)
    assert w.check("a", now=0)[0]
    assert not w.check("a", now=59)[0]
    assert w.check("a", now=61)[0]


def test_instance_cap_protects_the_key_from_many_visitors():
    w = SlidingWindow(limit=5, window_s=60, instance_limit=3)
    assert all(w.check(v, now=0)[0] for v in ("a", "b", "c"))
    assert not w.check("d", now=1)[0]
