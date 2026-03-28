from support_queue_env.server.support_queue_environment import SupportQueueEnvironment

print("Testing difficulty-scaled max_steps:\n")

tests = [
    ("easy_password_reset", 4),
    ("medium_duplicate_charge", 6),
    ("hard_admin_compromise", 8),
]

all_pass = True
for task_id, expected_steps in tests:
    env = SupportQueueEnvironment()
    obs = env.reset(task_id=task_id)
    actual = obs.max_steps
    status = "✓" if actual == expected_steps else "✗"
    if actual != expected_steps:
        all_pass = False
    print(f"{status} {task_id}: {actual} steps (expected {expected_steps})")

if all_pass:
    print("\n✅ All difficulty-scaled steps working correctly!")
else:
    print("\n❌ Some tests failed!")
