class FakeDocumentSnapshot:
    def __init__(self, data):
        self._data = data

    @property
    def exists(self) -> bool:
        return self._data is not None

    def to_dict(self):
        return dict(self._data) if self._data is not None else None


class FakeDocumentReference:
    def __init__(self, store, collection, doc_id):
        self._store = store
        self._collection = collection
        self._id = doc_id

    def get(self):
        return FakeDocumentSnapshot(self._store.get((self._collection, self._id)))

    def set(self, data, merge=False):
        key = (self._collection, self._id)
        if merge and key in self._store:
            self._store[key] = {**self._store[key], **data}
        else:
            self._store[key] = dict(data)

    def update(self, data):
        key = (self._collection, self._id)
        self._store[key] = {**self._store.get(key, {}), **data}


class FakeCollectionReference:
    def __init__(self, store, name):
        self._store = store
        self._name = name

    def document(self, doc_id):
        return FakeDocumentReference(self._store, self._name, doc_id)

    def stream(self):
        return [
            FakeDocumentSnapshot(data)
            for (coll, _id), data in self._store.items()
            if coll == self._name
        ]

    def add(self, data):
        n = sum(1 for c, _ in self._store if c == self._name)
        ref = FakeDocumentReference(self._store, self._name, f"auto{n + 1}")
        ref.set(data)
        return ref


class FakeTransaction:
    def __init__(self, store):
        self._store = store
        self._read_only = False
        self._max_attempts = 5
        self._id = "fake-txn-id"

    def _clean_up(self):
        pass

    def _begin(self, retry_id=None):
        pass

    def _commit(self):
        pass

    def _rollback(self):
        pass

    def get(self, ref):
        return ref.get()

    def update(self, ref, data):
        ref.update(data)


class FakeFirestore:
    def __init__(self):
        self._store = {}

    def collection(self, name):
        return FakeCollectionReference(self._store, name)

    def run_transaction(self, fn):
        return fn(FakeTransaction(self._store))

    def transaction(self):
        return FakeTransaction(self._store)
