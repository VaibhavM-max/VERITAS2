from ledger.crypto import sha256_hash
from ledger.merkle import MerkleAccumulator


def test_merkle_root_and_inclusion() -> None:
    tree = MerkleAccumulator()
    leaves = [sha256_hash(f"leaf-{index}".encode()) for index in range(5)]
    for leaf in leaves:
        tree.add(leaf)
    assert tree.get_leaf_count() == 5
    assert tree.root
    assert all(tree.verify_inclusion(leaf, tree.root) for leaf in leaves)
