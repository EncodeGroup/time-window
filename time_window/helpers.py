def make_sequence(elements):
    """
    Ensure that elements is a type of sequence, otherwise
    it converts it to a list with only one element.
    """
    if isinstance(elements, (list, set, tuple)):
        return elements
    elif elements is None:
        return []
    else:
        return [elements]


def gaps_iterator(seq):
    """
    Iterate on the gaps between elements of the sequence. Each time a new item
    is requested a tuple with the next two sequential elements is returned.

    Example:
     [3,4,5,6] -> [(3,4), (4,5), (5,6)]
    """
    it = iter(seq)
    try:
        previous = next(it)
    except StopIteration:
        return

    while True:
        try:
            current = next(it)
            yield (previous, current)
            previous = current
        except StopIteration:
            return
