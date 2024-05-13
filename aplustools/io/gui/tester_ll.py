@classmethod
def _loadImagesAroundIndex(cls, target, index, images: List[QScalingGraphicPixmapItem]):
    images[index].ensure_loaded()

    first_loaded_index = last_loaded_index = 0
    i = j = index
    for i, item in enumerate(images[index + 1:]):
        if cls._isVisibleInViewport(target, item):
            target.thread_pool.submit(item.ensure_loaded)
        else:
            item.ensure_unloaded()
            break
    last_loaded_index = i + index + 1
    for j, item in enumerate(images[index::-1]):
        if cls._isVisibleInViewport(target, item):
            target.thread_pool.submit(item.ensure_loaded)
        else:
            item.ensure_unloaded()
            break
    first_loaded_index = index - j

    num_buffer_images = 2

    for ind in range(last_loaded_index + 1, last_loaded_index + num_buffer_images):
        if len(images) > ind:
            target.thread_pool.submit(images[ind].ensure_loaded)

    for ind in range(first_loaded_index - 1, first_loaded_index - num_buffer_images):
        if len(images) > ind > 0:
            target.thread_pool.submit(images[ind].ensure_loaded)
