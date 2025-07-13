"""TBA"""

import typing
from concurrent.futures import (
    ThreadPoolExecutor as _ThreadPoolExecutor,
    Future as _Future,
)

# We basically need to change the way the threads work and thus need these
from concurrent.futures.thread import _threads_queues, _shutdown, _base
from threading import (
    Event as _Event,
    Lock as _TLock,
    Thread as _Thread,
    current_thread as _current_thread,
)
from multiprocessing.shared_memory import SharedMemory as _SharedMemory
from multiprocessing.synchronize import RLock as _RMLockT
from multiprocessing import RLock as _RMLock
import weakref
import struct
import queue
import re

from .env import MAX_PATH  # as a reference to be importable from here too
from .env import auto_repr as _auto_repr
from ..package import enforce_hard_deps as _enforce_hard_deps
from ..package.chronokit import FlexTimer as _TimidTimer

# Standard typing imports for aps
import typing_extensions as _te
import collections.abc as _a
import typing as _ty

if _ty.TYPE_CHECKING:
    import _typeshed as _tsh
import types as _ts

__deps__: list[str] = []
__hard_deps__: list[str] = []
_enforce_hard_deps(__hard_deps__, __name__)


@_auto_repr
class _SharedReference:
    """Shared reference to memory and a lock. It can get pickled and send between processes"""

    def __init__(self, struct_format: str, shm_name: str, lock: _RMLockT) -> None:
        self.struct_format: str = struct_format
        self.shm_name: str = shm_name
        self.lock = _MPLock = lock
        # self._ss: "SharedStruct | None" = None

    def dereference(self) -> "SharedStruct":
        return SharedStruct.from_reference(self)

    # def set_field(self, index: int, value: _ty.Any) -> None:
    #     """
    #     Set a single field in the shared memory structure.
    #     :param index: Index of the field to set (starting from 0).
    #     :param value: The value to set, matching the struct format at the specified index.
    #     """
    #     if self._ss is None:
    #         raise RuntimeError("You can't set a field outside the context manager")
    #     self._ss.set_field(index, value)
    #
    # def get_field(self, index: int) -> _ty.Any:
    #     """
    #     Get a single field from the shared memory structure.
    #     :param index: Index of the field to get (starting from 0).
    #     :return: The value of the field, unpacked based on the struct format.
    #     """
    #     if self._ss is None:
    #         raise RuntimeError("You can't get a field outside the context manager")
    #     return self._ss.get_field(index)
    #
    # def __enter__(self) -> _ty.Self:
    #     if self._ss is None:
    #         self._ss = SharedStruct.from_reference(self)
    #     self._ss.set_lock()
    #     return self
    #
    # def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
    #     if self._ss is None:
    #         raise RuntimeError(f"Private attribute was changed during context manager")
    #     self._ss.unset_lock()
    #     return False
    #
    # def close(self) -> None:
    #     if hasattr(self, "_ss") and self._ss is not None:
    #         self._ss.close()
    #         self._ss = None
    #
    # def __del__(self) -> None:
    #     self.close()


def _split_struct_format(fmt: str) -> list[str]:
    """
    Splits a struct format string like "i10sH" into components like ["i", "10s", "H"].
    :param fmt: The struct format string, compact or spaced.
    :return: List of format components.
    """
    # Regex: match an optional number prefix + single format character or special format
    pattern = re.compile(r"(\d*[xcbB?hHiIlLqQnNefdspP])")
    matches = pattern.findall(fmt)

    remainder = pattern.sub("", fmt)
    if remainder.strip():
        raise ValueError(f"Unrecognized struct format parts in: {remainder!r}")

    return matches


class SharedStruct:
    """Shared memory through processes"""

    REFERENCE = _SharedReference  # For typing

    def __init__(
        self,
        struct_format: str,
        create: bool = False,
        shm_name: str | None = None,
        *_,
        overwrite_mp_lock: _RMLockT | None = None,
    ) -> None:
        self._struct_format: str = struct_format
        self._struct_parts: list[str] = _split_struct_format(struct_format)
        self._struct_size: int = struct.calcsize(struct_format)

        if isinstance(overwrite_mp_lock, _RMLockT):
            self._lock: _RMLockT = overwrite_mp_lock
        else:
            self._lock: _RMLockT = _RMLock()

        if create:  # Create a new, shared memory segment
            self._shm: _SharedMemory = _SharedMemory(
                create=True, size=self._struct_size
            )
        else:  # Attach to an existing shared memory segment
            if shm_name is None:
                raise ValueError("shm_name must be provided, when create=False")
            self._shm: _SharedMemory = _SharedMemory(name=shm_name)
        self._shm_name: str = (
            self._shm.name
        )  # Store the shared memory name for reference

    def set_data(self, *values) -> None:
        """
        Set data in the shared memory structure.
        :param values: Values to set, matching the struct format.
        """
        if len(values) != len(self._struct_parts):
            raise ValueError("Number of values must match the struct format")
        with self._lock:
            packed_data = struct.pack(self._struct_format, *values)
            self._shm.buf[: self._struct_size] = packed_data

    def get_data(self) -> tuple[_ty.Any, ...]:
        """
        Get data from the shared memory structure.
        :return: Tuple of values unpacked from the shared memory.
        """
        with self._lock:
            packed_data = self._shm.buf[: self._struct_size]
            return struct.unpack(self._struct_format, packed_data)

    def set_field(self, index: int, value: _ty.Any) -> None:
        """
        Set a single field in the shared memory structure.
        :param index: Index of the field to set (starting from 0).
        :param value: The value to set, matching the struct format at the specified index.
        """
        if index < 0 or index >= len(self._struct_parts):
            raise IndexError("Field index out of range")
        # Calculate offset for the field based on the format
        offset = sum(struct.calcsize(fmt) for fmt in self._struct_parts[:index])
        field_format = self._struct_parts[index]
        field_size = struct.calcsize(field_format)
        with self._lock:
            packed_field = struct.pack(field_format, value)
            self._shm.buf[offset : offset + field_size] = packed_field

    def get_field(self, index: int) -> _ty.Any:
        """
        Get a single field from the shared memory structure.
        :param index: Index of the field to get (starting from 0).
        :return: The value of the field, unpacked based on the struct format.
        """
        if index < 0 or index >= len(self._struct_parts):
            raise IndexError("Field index out of range")
        offset = sum(struct.calcsize(fmt) for fmt in self._struct_parts[:index])
        field_format = self._struct_parts[index]
        field_size = struct.calcsize(field_format)
        with self._lock:
            packed_field = self._shm.buf[offset : offset + field_size]
            return struct.unpack(field_format, packed_field)[0]

    def reference(self) -> _SharedReference:
        """References this shared struct in a simpler data structure"""
        return _SharedReference(self._struct_format, self._shm_name, self._lock)

    @classmethod
    def from_reference(cls, ref: _SharedReference) -> _te.Self:
        """Loads a shared struct obj from a shared reference"""
        return cls(ref.struct_format, False, ref.shm_name, overwrite_mp_lock=ref.lock)

    def close(self) -> None:
        """
        Close the shared memory segment.
        """
        self._shm.close()

    def unlink(self) -> None:
        """
        Unlock the shared memory segment (only call this if you own the memory).
        """
        self._shm.unlink()

    def set_lock(self) -> None:
        """Sets the lock for multiple operations."""
        self._lock.acquire()

    def unset_lock(self) -> None:
        """Unsets the lock."""
        self._lock.release()

    def __enter__(self) -> _te.Self:
        self.set_lock()
        return self

    def __exit__(
        self,
        exc_type: _ty.Type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: BaseException | None,
    ) -> bool | None:
        self.unset_lock()
        # If an exception occurred, propagate it by returning False (default behavior).
        return False  # Exception will propagate to the caller

    def __repr__(self) -> str:
        return (
            f"SharedStruct(struct_format='{self._struct_format}', struct_size={self._struct_size}, "
            f"shm_name='{self._shm_name}')"
        )


_T = _ty.TypeVar("_T")


class ThreadSafeList(list[_T], _ty.Generic[_T]):
    """
    A thread-safe implementation of a Python list, ensuring that all mutation operations are protected by a lock.

    This class extends the built-in Python `list` and overrides key methods to ensure that operations like
    appending, removing, setting items, and modifying the list are thread-safe. It uses a lock (`_TLock`)
    to synchronize access, making it safe for use in multithreaded environments.

    This class is useful when you need a list that can be shared between threads and you want to prevent
    race conditions when modifying the list. Read operations such as `__getitem__` and `__len__` are also
    protected for full thread safety, though read-only operations are generally safe unless done concurrently
    with writes.
    """

    def __init__(self, *args: _ty.Any, **kwargs: _ty.Any) -> None:
        super().__init__(*args, **kwargs)
        self._lock: _TLock = _TLock()

    def append(self, item: _T) -> None:
        with self._lock:
            super().append(item)

    def extend(self, iterable: _ty.Iterable[_T]) -> None:
        with self._lock:
            super().extend(iterable)

    def insert(self, index: int, item: _T) -> None:
        with self._lock:
            super().insert(index, item)

    def remove(self, item: _T) -> None:
        with self._lock:
            super().remove(item)

    def pop(self, index: int = -1) -> _T:
        with self._lock:
            return super().pop(index)

    def clear(self) -> None:
        with self._lock:
            super().clear()

    def index(self, item: _T, *args) -> int:
        with self._lock:
            return super().index(item, *args)

    def count(self, item: _T) -> int:
        with self._lock:
            return super().count(item)

    def sort(self, *, key=None, reverse: bool = False) -> None:
        with self._lock:
            super().sort(key=key, reverse=reverse)

    def reverse(self) -> None:
        with self._lock:
            super().reverse()

    def copy(self) -> list[_T]:
        with self._lock:
            return super().copy()

    def __getitem__(self, index: _ty.Union[int, slice]) -> _ty.Union[_T, list[_T]]:
        with self._lock:
            return super().__getitem__(index)

    def __setitem__(
        self, index: _ty.Union[int, slice], value: _ty.Union[_T, _ty.Iterable[_T]]
    ) -> None:
        with self._lock:
            super().__setitem__(index, value)

    def __delitem__(self, index: _ty.Union[int, slice]) -> None:
        with self._lock:
            super().__delitem__(index)

    def __len__(self) -> int:
        with self._lock:
            return super().__len__()

    def __iter__(self) -> _ty.Iterator[_T]:
        with self._lock:
            return iter(super().copy())  # Safe iteration on a copy

    def __contains__(self, item: _T) -> bool:
        with self._lock:
            return super().__contains__(item)

    def __eq__(self, other) -> bool:
        with self._lock:
            return super().__eq__(other)

    def __repr__(self) -> str:
        with self._lock:
            return super().__repr__()

    def __str__(self) -> str:
        with self._lock:
            return super().__str__()


def _self_managing_worker(
    executor_reference,
    work_queue,
    signal_func: _a.Callable[[_Thread, _Event], None],
    initializer,
    initargs,
) -> None:
    shutdown_event: _Event = _Event()

    if initializer is not None:
        try:
            initializer(*initargs)
        except BaseException:
            _base.LOGGER.critical("Exception in initializer:", exc_info=True)
            executor = executor_reference()
            if executor is not None:
                executor._initializer_failed()
            return
    try:
        while True:
            try:
                work_item = work_queue.get_nowait()
            except queue.Empty:
                # attempt to increment idle count if queue is empty
                executor = executor_reference()
                if executor is not None:
                    # Call the signal function to check if we should scale down
                    signal_func(_current_thread(), shutdown_event)

                    # Check if this thread should shut down
                    if shutdown_event.is_set():
                        _base.LOGGER.info("Shutting down worker thread")
                        del executor
                        return  # Graceful shutdown
                    executor._idle_semaphore.release()  # Signal idle thread available
                del executor
                work_item = work_queue.get(block=True)

            if work_item is not None:
                work_item.run()
                # Delete references to object. See GH-60488
                del work_item
                continue

            executor = executor_reference()
            # Exit if:
            #   - The interpreter is shutting down OR
            #   - The executor that owns the worker has been collected OR
            #   - The executor that owns the worker has been shutdown.
            if _shutdown or executor is None or executor._shutdown:
                # Flag the executor as shutting down as early as possible if it
                # is not gc-ed yet.
                if executor is not None:
                    executor._shutdown = True
                # Notice other workers
                work_queue.put(None)
                return
            del executor
    except BaseException:
        _base.LOGGER.critical("Exception in worker", exc_info=True)


class HyperScalingDynamicThreadPoolExecutor(_ThreadPoolExecutor):
    """
    A highly dynamic thread pool executor that rapidly scales the number of worker threads based on workload demand.

    This executor adjusts the number of threads between a minimum and maximum range, with a focus on rapid scaling
    up and down. Idle threads are aggressively cleaned up at regular intervals to ensure optimal resource management.
    The pool dynamically and quickly scales the number of active threads according to the task load.

    Attributes:
        _min_workers (int): The minimum number of worker threads that should always remain active.
        _max_workers (int | None): The maximum number of worker threads allowed in the pool. If None, the number of
                                  workers can grow indefinitely based on the workload.
        _check_interval (float): The interval (in seconds) between checks for idle threads to join or remove. Lower values
                                lead to more frequent checks and faster thread scaling.
        _thread_name_prefix (str): Optional prefix to name the worker threads, useful for identifying threads in logs or
                                  debugging.
        _initializer (Callable): A callable that initializes each worker thread when it is created, useful for setting up
                                thread-specific state (e.g., opening a database connection).
        _initargs (tuple): A tuple of arguments to pass to the `initializer` callable for initializing worker threads.

    Example:
        executor = HyperDynamicThreadPoolExecutor(min_workers=2, max_workers=100, check_interval=0.1)
        executor.submit(task_function)

    Methods:
        _join_threads(): Private method that checks the pool for idle threads and aggressively joins (terminates) them
                         to release resources.
        shutdown(wait=True, cancel_futures=False): Gracefully shuts down the thread pool by joining all threads and
                                                   optionally canceling pending futures.

    Notes:
        - This class is designed for environments where the workload fluctuates rapidly, and thread management needs to
          respond quickly to avoid over or under-utilization of resources.
        - It uses a timer to aggressively check and join idle threads at the defined `check_interval`, allowing for
          faster scaling compared to other thread pool implementations.
        - The `_lock` attribute ensures that thread pool modifications (such as joining threads or resizing the pool) are
          thread-safe.

    """

    def __init__(
        self,
        min_workers: int = 0,
        max_workers: int | None = None,
        check_interval: float = 1.0,
        thread_name_prefix: str = "",
        initializer: _a.Callable[[object | None], None] = None,
        initargs: tuple[_ty.Any, ...] = (),
    ) -> None:
        super().__init__(max_workers, thread_name_prefix, initializer, initargs)
        self._min_workers = min_workers
        self._check_interval: float = check_interval
        self._check_timer: _TimidTimer = _TimidTimer(start_now=False)
        self._check_timer.loop(check_interval, self._join_threads, daemon=True)
        self._lock: _TLock = _TLock()
        self._to_join: set = set()
        self._worker_func: _a.Callable = _self_managing_worker

    @property
    def _should_scale_down(self) -> bool:
        """
        Checks if the number of idle threads is higher than the minimum number required.
        :return: If more threads are idle than are required to be.
        """
        return self._idle_semaphore._value >= self._min_workers

    def _join_threads(self) -> None:
        with self._lock:
            threads = self._to_join.copy()
            self._to_join.clear()
        for thread in threads:
            thread.join()

    def _should_shutdown(self, thread: _Thread, shutdown_event: _Event) -> None:
        if self._should_scale_down:
            with self._lock:
                shutdown_event.set()
                self._threads.remove(thread)
                del _threads_queues[thread]
                self._to_join.add(thread)

    def _adjust_thread_count(self) -> None:
        # if idle threads are available, don't spin new threads
        if self._idle_semaphore.acquire(timeout=0):
            return

        # When the executor gets lost, the weakref callback will wake up
        # the worker threads.
        def weakref_cb(_, q=self._work_queue):
            q.put(None)

        num_threads = len(self._threads)
        if num_threads < self._max_workers:
            thread_name = "%s_%d" % (self._thread_name_prefix or self, num_threads)
            t = _Thread(
                name=thread_name,
                target=self._worker_func,
                args=(
                    weakref.ref(self, weakref_cb),
                    self._work_queue,
                    self._should_shutdown,
                    self._initializer,
                    self._initargs,
                ),
            )
            t.start()
            with self._lock:
                self._threads.add(t)
                _threads_queues[t] = self._work_queue

    def shutdown(self, wait: bool = True, *, cancel_futures: bool = False) -> None:
        """
        Clean-up the resources associated with the Executor.  It is safe to call this method several times.
        Otherwise, no other methods can be called after this one.  Args: wait: If True then shutdown will not return
        until all running futures have finished executing and the resources used by the executor have been reclaimed.
        cancel_futures: If True then shutdown will cancel all pending futures. Futures that are completed or running
        will not be cancelled.

        :param wait: If True then shutdown will not return until all running futures have finished executing and the resources used by the executor have been reclaimed.
        :param cancel_futures: If True then shutdown will cancel all pending futures. Futures that are completed or running will not be cancelled.
        :return:
        """
        with self._lock:
            super().shutdown(wait, cancel_futures=cancel_futures)
        self._check_timer.stop_loops(0, not_exists_okay=True)

    def __del__(self) -> None:
        self.shutdown()


class _ExitWorkerFlag: ...


def _lazy_worker(
    executor_reference,
    work_queue,
    signal_func: _a.Callable[[_Thread, _Event], None],
    initializer,
    initargs,
):
    shutdown_event: _Event = _Event()

    if initializer is not None:
        try:
            initializer(*initargs)
        except BaseException:
            _base.LOGGER.critical("Exception in initializer:", exc_info=True)
            executor = executor_reference()
            if executor is not None:
                executor._initializer_failed()
            return
    try:
        while True:
            try:
                work_item = work_queue.get_nowait()
                if work_item is _ExitWorkerFlag:
                    raise queue.Empty
            except queue.Empty:
                # attempt to increment idle count if queue is empty
                executor = executor_reference()
                if executor is not None:
                    executor._idle_semaphore.release()  # Signal idle thread available
                del executor
                work_item = work_queue.get(block=True)

            if isinstance(work_item, _ExitWorkerFlag):
                # Call the signal function to check if we should scale down
                signal_func(_current_thread(), shutdown_event)

                # Check if this thread should shut down
                if shutdown_event.is_set():
                    _base.LOGGER.info("Shutting down worker thread")
                    return  # Graceful shutdown
            elif work_item is not None:
                work_item.run()
                # Delete references to object. See GH-60488
                del work_item
                continue

            executor = executor_reference()
            # Exit if:
            #   - The interpreter is shutting down OR
            #   - The executor that owns the worker has been collected OR
            #   - The executor that owns the worker has been shutdown.
            if _shutdown or executor is None or executor._shutdown:
                # Flag the executor as shutting down as early as possible if it
                # is not gc-ed yet.
                if executor is not None:
                    executor._shutdown = True
                # Notice other workers
                work_queue.put(None)
                return
            del executor
    except BaseException:
        _base.LOGGER.critical("Exception in worker", exc_info=True)


class LazyDynamicThreadPoolExecutor(HyperScalingDynamicThreadPoolExecutor):
    """
    A thread pool executor that dynamically manages a pool of worker threads, with a lazy scaling mechanism.

    This executor adjusts the number of threads between a minimum and maximum range, scaling the pool size
    based on the workload and checking for idle threads at regular intervals. Idle threads are joined and
    cleaned up when necessary. The thread pool lazily adjusts its size, meaning it only scales up or down
    as required by the task load.

    Configurations known to work well are (min_workers, max_workers, max_join_number, check_interval):
    - (5, 100-200, 10, 2.0)
    - (5, 100-200, 5, 1.0)
    - (2, 10, 5, 5.0)

    Attributes:
        _min_workers (int): The minimum number of worker threads that should always remain active.
        _max_workers (int | None): The maximum number of worker threads allowed in the pool. If None, the number of
                                  workers can grow indefinitely based on the workload.
        _check_interval (float): The interval (in seconds) between checks for idle threads to join.
        _max_join_number (int): The maximum number of threads to be joined in one pass during the idle check.
        _thread_name_prefix (str): Optional prefix to name the worker threads. Helps in identifying threads in logs.
        _initializer (Callable): A callable that initializes each worker thread when it is created. This is useful for
                                setting up thread-specific state (e.g., opening a database connection).
        _initargs (tuple): A tuple of arguments to pass to the `initializer` callable for initializing worker threads.

    Example:
        executor = LazyDynamicThreadPoolExecutor(min_workers=2, max_workers=10, check_interval=1.0)
        executor.submit(task_function)

    Methods:
        _join_threads(): Private method that checks the pool for idle threads and joins them to release resources.
        shutdown(wait=True, cancel_futures=False): Gracefully shuts down the thread pool by joining all threads
                                                   and optionally canceling pending futures.

    Notes:
        - This class uses a timer to periodically check for idle threads and manages resources efficiently by
          dynamically adjusting the thread pool size based on the workload.
        - The `_lock` attribute ensures that thread pool modifications (such as joining threads or resizing the pool)
          are thread-safe.
    """

    def __init__(
        self,
        min_workers: int = 0,
        max_workers: int | None = None,
        check_interval: float = 1.0,
        max_join_number: int = 5,
        thread_name_prefix: str = "",
        initializer: _a.Callable[[object | None], None] = None,
        initargs: tuple[_ty.Any, ...] = (),
    ) -> None:
        super().__init__(
            min_workers,
            max_workers,
            check_interval,  # Never used
            thread_name_prefix,
            initializer,
            initargs,
        )
        self._max_join_number: int = max_join_number
        self._join_count = 0  # Start at valid state
        self._worker_func: _a.Callable = _lazy_worker

    def _join_threads(self) -> None:
        if self._work_queue.qsize() == 0:
            with self._lock:
                threads = self._to_join.copy()
                self._to_join.clear()
            self._join_count = 0
            for _ in range(self._max_join_number):
                if self._idle_semaphore.acquire(timeout=0):
                    self._work_queue.put(_ExitWorkerFlag())
            for thread in threads:
                thread.join()

    def _should_shutdown(self, thread: _Thread, shutdown_event: _Event) -> None:
        if self._should_scale_down and 0 <= self._join_count < self._max_join_number:
            with self._lock:
                self._join_count += 1
                shutdown_event.set()
                self._threads.remove(thread)
                del _threads_queues[thread]
                self._to_join.add(thread)


class LazySelfManagingDynamicThreadPoolExecutor(LazyDynamicThreadPoolExecutor):
    """
    A self-managing dynamic thread pool executor that lazily scales worker threads based on workload demands.

    This thread pool dynamically adjusts the number of active worker threads between a specified minimum and maximum.
    Each worker thread autonomously monitors its own workload and decides whether to terminate if no tasks are available,
    leading to efficient resource management. The pool lazily scales up or down as tasks are added or completed.

    Attributes:
        _min_workers (int): The minimum number of worker threads that should always remain active.
        _max_workers (int | None): The maximum number of worker threads allowed in the pool. If None, the number of
                                   workers can grow indefinitely based on the workload.
        _check_interval (float): The interval (in seconds) between idle thread checks.
        _max_join_number (int): The maximum number of idle threads that can be joined in one pass during the idle check.
        _thread_name_prefix (str): Optional prefix to name the worker threads for easier identification in logs.
        _initializer (Callable): A callable to initialize each worker thread when it is created, useful for setting up
                                 thread-specific resources (e.g., opening database connections).
        _initargs (tuple): A tuple of arguments to pass to the `initializer` callable.

    Example:
        executor = LazySelfManagingDynamicThreadPoolExecutor(min_workers=2, max_workers=10, check_interval=1.0)
        executor.submit(task_function)

    Methods:
        _lazy_self_reporting_worker(): Private worker method where each thread monitors its workload, reports idle state,
                                       and determines whether to shut down when there are no tasks.
        _join_threads(): Private method that checks for idle threads and joins them to release resources.
        shutdown(wait=True, cancel_futures=False): Gracefully shuts down the thread pool by joining all threads
                                                   and optionally canceling pending futures.

    Notes:
        - Each worker thread autonomously reports its state and handles its lifecycle (lazy termination) when idle,
          contributing to efficient resource usage.
        - The class periodically checks for idle threads and manages resources by dynamically resizing the pool as needed.
        - Thread pool modifications (e.g., joining threads or resizing) are thread-safe due to the use of a `_lock` attribute.
    """

    def __init__(
        self,
        min_workers: int = 0,
        max_workers: int | None = None,
        check_interval: float = 1.0,
        max_join_number: int = 5,
        thread_name_prefix: str = "",
        initializer: _a.Callable[[object | None], None] = None,
        initargs: tuple[_ty.Any, ...] = (),
    ) -> None:
        super().__init__(
            min_workers,
            max_workers,
            check_interval,
            max_join_number,
            thread_name_prefix,
            initializer,
            initargs,
        )
        self._worker_func: _a.Callable = _self_managing_worker

    def _join_threads(self) -> None:
        if self._work_queue.qsize() == 0 and self._idle_semaphore._value == len(
            self._threads
        ):
            with self._lock:
                threads = self._to_join.copy()
                self._to_join.clear()
            self._join_count = 0
            for _ in range(self._max_join_number):
                self._work_queue.put(None)  # Wake up threads
            for thread in threads:
                thread.join()

    def _should_shutdown(self, thread: _Thread, shutdown_event: _Event) -> None:
        if self._should_scale_down and 0 <= self._join_count < self._max_join_number:
            with self._lock:
                if self._idle_semaphore.acquire(timeout=0):
                    self._join_count += 1
                    shutdown_event.set()
                    self._threads.remove(thread)
                    del _threads_queues[thread]
                    self._to_join.add(thread)


class SharedLDTPE(LazyDynamicThreadPoolExecutor):
    def __init__(self) -> None:
        raise NotImplementedError(
            "LazyDynamicThreadPoolExecutor is not implemented yet"
        )

    def create_handle(self) -> int: ...

    def reserve(self, amount_of_threads: int, handle: int) -> None: ...

    def submit(self, task, handle: int) -> None: ...
