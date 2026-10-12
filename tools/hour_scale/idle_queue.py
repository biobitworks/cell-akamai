"""Wait for an idle existing endpoint, then execute a pinned runner once.

No deployment changes or inference requests occur in this module.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time


def idle_duration(previous, now, idle):
    start = (now if previous is None else previous) if idle else None
    return start, 0 if start is None else now - start


def endpoint_idle(sample):
    return sample.get('running') == 0 and sample.get('waiting') == 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--dataset-root', type=Path, required=True)
    parser.add_argument('--run-root', type=Path, required=True)
    parser.add_argument('--source-sha', required=True)
    args = parser.parse_args()
    source = args.source.resolve()
    # Compile before waiting; never manufacture executable source by replacement.
    subprocess.run([os.sys.executable, '-m', 'py_compile', str(source)], check=True)
    import sys
    sys.path.insert(0, str(source.parent))
    from sustained import metrics
    from runner import atomic
    state = args.run_root.with_suffix('.queue.json')
    stop = args.run_root.with_suffix('.STOP')
    since = None
    while not stop.exists():
        sample = metrics()
        since, elapsed = idle_duration(since, time.monotonic(),
                                       endpoint_idle(sample))
        atomic(state, {'state': 'WAITING_FOR_60S_CONTINUOUS_IDLE',
                       'idle_seconds': elapsed, 'no_inference_submitted': True})
        if elapsed >= 60:
            env = dict(os.environ, CAKM_SOURCE_SHA=args.source_sha,
                       CAKM_DATASET_ROOT=str(args.dataset_root),
                       CAKM_RUN_ROOT=str(args.run_root))
            os.execve(os.sys.executable, [os.sys.executable, str(source)], env)
        time.sleep(5)
    atomic(state, {'state': 'STOPPED_BEFORE_INFERENCE', 'no_inference_submitted': True})


if __name__ == '__main__':
    main()
