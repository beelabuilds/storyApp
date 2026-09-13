"""IPC Manager connecting FastAPI to the Qwen Worker process.

Uses multiprocessing.Queue for bidirectional communication with correlation IDs
and thread-safe dispatching so FastAPI's async event loop never blocks.
"""

import os
import sys
import uuid
import asyncio
import threading
import logging
import multiprocessing as mp
from pathlib import Path
from typing import Dict, Any, Optional

# Ensure project root is in sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ai.qwen_worker import run_qwen_worker

logger = logging.getLogger("qwen_ipc")


class QwenIPCManager:
    """Manages the lifecycle of the Qwen worker process and handles IPC dispatch."""

    def __init__(self):
        self.worker_process: Optional[mp.Process] = None
        self.request_queue: Optional[mp.Queue] = None
        self.response_queue: Optional[mp.Queue] = None
        self.stop_event: Optional[mp.Event] = None
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.reader_thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._running = False

    def start(self, model_path: Optional[str] = None):
        """Start the Qwen worker process and response reader thread."""
        if self._running:
            logger.info("Qwen worker is already running.")
            return

        logger.info("Initializing Qwen IPC queues and worker process...")
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            self._loop = asyncio.get_event_loop()

        # On Windows, spawn is used by default. Queues must be created via context
        ctx = mp.get_context()
        self.request_queue = ctx.Queue()
        self.response_queue = ctx.Queue()
        self.stop_event = ctx.Event()

        self.worker_process = ctx.Process(
            target=run_qwen_worker,
            args=(
                self.request_queue,
                self.response_queue,
                self.stop_event,
                model_path,
            ),
            daemon=True,
            name="QwenWorkerProcess",
        )
        self.worker_process.start()
        self._running = True

        # Start non-blocking response reader thread
        self.reader_thread = threading.Thread(
            target=self._reader_loop,
            daemon=True,
            name="QwenIPCResponseReader",
        )
        self.reader_thread.start()
        logger.info("Qwen worker started successfully (PID: %s)", self.worker_process.pid)

    def _reader_loop(self):
        """Background thread reading responses from the worker without blocking FastAPI."""
        while self._running and self.response_queue and not self.stop_event.is_set():
            try:
                # Poll response queue with small timeout
                try:
                    response = self.response_queue.get(timeout=0.2)
                except Exception:
                    continue

                if response is None:
                    break

                corr_id = response.get("correlation_id")
                if corr_id and self._loop and not self._loop.is_closed():
                    self._loop.call_soon_threadsafe(self._resolve_request, corr_id, response)

            except Exception as e:
                if self._running:
                    logger.error("Error in response reader loop: %s", e)

    def _resolve_request(self, corr_id: str, response: Dict[str, Any]):
        """Resolve the pending future on the event loop."""
        future = self.pending_requests.pop(corr_id, None)
        if future and not future.done():
            future.set_result(response)

    async def generate_story(
        self,
        description: str,
        age: Optional[str] = None,
        hero: Optional[str] = None,
        feedback_prompt: Optional[str] = None,
        max_tokens: int = 1100,
        timeout: float = 120.0,
    ) -> Dict[str, Any]:
        """Send story request to Qwen worker and await response non-blockingly."""
        if not self._running or not self.worker_process or not self.worker_process.is_alive():
            raise RuntimeError("Qwen worker process is not running.")

        corr_id = str(uuid.uuid4())
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self.pending_requests[corr_id] = future

        task = {
            "correlation_id": corr_id,
            "description": description,
            "age": age,
            "hero": hero,
            "feedback_prompt": feedback_prompt,
            "max_tokens": max_tokens,
        }

        # Put request in queue asynchronously via to_thread to prevent blocking
        await asyncio.to_thread(self.request_queue.put, task)

        try:
            result = await asyncio.wait_for(future, timeout=timeout)
            return result
        except asyncio.TimeoutError:
            self.pending_requests.pop(corr_id, None)
            raise TimeoutError(f"Qwen worker timed out after {timeout}s.")
        except Exception as e:
            self.pending_requests.pop(corr_id, None)
            raise e

    def is_alive(self) -> bool:
        """Check if worker process is active."""
        return bool(self._running and self.worker_process and self.worker_process.is_alive())

    def stop(self):
        """Clean shutdown of the worker process and reader thread."""
        if not self._running:
            return

        logger.info("Stopping Qwen worker process...")
        self._running = False

        if self.stop_event:
            self.stop_event.set()

        if self.request_queue:
            try:
                self.request_queue.put(None)
            except Exception:
                pass

        if self.response_queue:
            try:
                self.response_queue.put(None)
            except Exception:
                pass

        if self.worker_process and self.worker_process.is_alive():
            self.worker_process.join(timeout=3.0)
            if self.worker_process.is_alive():
                logger.warning("Worker did not exit within timeout, terminating...")
                self.worker_process.terminate()
                self.worker_process.join(timeout=1.0)

        if self.reader_thread and self.reader_thread.is_alive():
            self.reader_thread.join(timeout=1.0)

        # Clear any remaining futures
        for corr_id, fut in list(self.pending_requests.items()):
            if not fut.done():
                fut.set_exception(RuntimeError("Worker shut down."))
        self.pending_requests.clear()

        logger.info("Qwen worker stopped.")


# Global singleton instance managed by FastAPI lifespan
qwen_manager = QwenIPCManager()
