import queue
import threading
import time
import logging
from typing import Dict, Any, Callable

logger = logging.getLogger("ContextOS.DaemonWorkers")

class DaemonWorkerPool:
    """
    Multi-Queue Priority Background Worker Pool.
    Priority Hierarchy:
    - P0: Realtime Critical Packet Validation (<2ms blocking)
    - P1: Event Ingestion (PostToolUse, Stop async non-blocking queue)
    - P2: Consolidation (Episodic -> Semantic memory)
    - P3: Shadow Experiments & Counterfactual Replay
    - P4: Integrity Audits (Drift, Provenance, Canary monitors)
    """
    def __init__(self):
        self.p1_ingest_queue = queue.Queue()
        self.p3_experiments_queue = queue.Queue()
        self.p4_integrity_queue = queue.Queue()
        self.is_running = False
        self._threads = []

    def enqueue_ingest(self, task: Callable[[], Any]):
        self.p1_ingest_queue.put(task)

    def enqueue_experiment(self, task: Callable[[], Any]):
        self.p3_experiments_queue.put(task)

    def enqueue_integrity(self, task: Callable[[], Any]):
        self.p4_integrity_queue.put(task)

    def start_workers(self):
        if self.is_running:
            return
        self.is_running = True

        # Worker 1: Ingestion & Consolidation Worker
        t1 = threading.Thread(target=self._worker_loop, args=("ingest_worker", self.p1_ingest_queue), daemon=True)
        # Worker 2: Shadow Experiments & Replay Worker
        t2 = threading.Thread(target=self._worker_loop, args=("experiment_worker", self.p3_experiments_queue), daemon=True)
        # Worker 3: Integrity & Canary Worker
        t3 = threading.Thread(target=self._worker_loop, args=("integrity_worker", self.p4_integrity_queue), daemon=True)

        self._threads = [t1, t2, t3]
        for t in self._threads:
            t.start()

    def _worker_loop(self, worker_name: str, target_queue: queue.Queue):
        while self.is_running:
            try:
                task = target_queue.get(timeout=1.0)
                if task:
                    try:
                        task()
                    except Exception as e:
                        logger.error(f"[{worker_name}] Error executing task: {e}")
                    finally:
                        target_queue.task_done()
            except queue.Empty:
                continue

    def stop_workers(self):
        self.is_running = False
        for t in self._threads:
            if t.is_alive():
                t.join(timeout=1.0)
