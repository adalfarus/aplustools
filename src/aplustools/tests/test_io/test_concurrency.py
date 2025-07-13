"""TBA"""

import time

from ...io.concurrency import *
import pytest

# Standard typing imports for aps
import typing_extensions as _te
import collections.abc as _a
import typing as _ty

if _ty.TYPE_CHECKING:
    import _typeshed as _tsh
import types as _ts


def test_shared_struct_creation_and_data_exchange() -> None:
    struct_format = "i f"
    ss = SharedStruct(struct_format, create=True)
    try:
        ss.set_data(42, 3.14)
        result = ss.get_data()
        assert result == (42, pytest.approx(3.14))
    finally:
        ss.close()
        ss.unlink()


def test_shared_struct_reference_and_restore() -> None:
    struct_format = "i f"
    ss1 = SharedStruct(struct_format, create=True)
    try:
        ss1.set_data(7, 2.71)
        ref = _SharedReference(ss1._struct_format, ss1._shm_name, ss1._lock)
        ss2 = SharedStruct(
            ref.struct_format, shm_name=ref.shm_name, overwrite_mp_lock=ref.lock
        )
        result = ss2.get_data()
        assert result == (7, pytest.approx(2.71))
        ss2.close()
    finally:
        ss1.close()
        ss1.unlink()


@pytest.mark.parametrize(
    "executor_cls",
    [
        HyperScalingDynamicThreadPoolExecutor,
        LazyDynamicThreadPoolExecutor,
        LazySelfManagingDynamicThreadPoolExecutor,
    ],
)
def test_executor_submit_and_shutdown(
    executor_cls: _ty.Type[HyperScalingDynamicThreadPoolExecutor],
) -> None:
    with executor_cls(min_workers=1, max_workers=4, check_interval=0.1) as executor:
        future = executor.submit(lambda x: x + 1, 41)
        assert future.result(timeout=2) == 42


@pytest.mark.parametrize(
    "executor_cls",
    [
        HyperScalingDynamicThreadPoolExecutor,
        LazyDynamicThreadPoolExecutor,
        LazySelfManagingDynamicThreadPoolExecutor,
    ],
)
def test_executor_map(
    executor_cls: _ty.Type[HyperScalingDynamicThreadPoolExecutor],
) -> None:
    with executor_cls(min_workers=2, max_workers=4, check_interval=0.1) as executor:
        results = list(executor.map(lambda x: x * x, range(5)))
        assert results == [0, 1, 4, 9, 16]


@pytest.mark.parametrize(
    "executor_cls",
    [
        HyperScalingDynamicThreadPoolExecutor,
        LazyDynamicThreadPoolExecutor,
        LazySelfManagingDynamicThreadPoolExecutor,
    ],
)
def test_executor_shutdown_blocks_future_submit(
    executor_cls: _ty.Type[HyperScalingDynamicThreadPoolExecutor],
) -> None:
    executor = executor_cls(min_workers=1, max_workers=2, check_interval=0.1)
    executor.submit(time.sleep, 0.1)
    executor.shutdown(wait=True)

    with pytest.raises(RuntimeError):
        executor.submit(lambda: 1)  # Post-shutdown usage raises a RuntimeError


# @pytest.mark.filterwarnings("ignore:PytestUnraisableExceptionWarning")
def test_SharedLDTPE() -> None:
    ...
    # with pytest.raises(NotImplementedError):
    #     shared = SharedLDTPE()
