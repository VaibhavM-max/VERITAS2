"""Deterministic Merkle accumulator for receipt inclusion checks."""

from ledger.crypto import sha256_hash


class MerkleAccumulator:
    def __init__(self) -> None:
        self.leaves: list[str] = []
        self.root = ""

    def add(self, leaf_hash: str) -> None:
        self.leaves.append(leaf_hash)
        self.root = self._compute_root()

    def _compute_root(self) -> str:
        if not self.leaves:
            return ""
        level = list(self.leaves)
        while len(level) > 1:
            if len(level) % 2:
                level.append(level[-1])
            level = [
                sha256_hash((level[index] + level[index + 1]).encode())
                for index in range(0, len(level), 2)
            ]
        return level[0]

    def verify_inclusion(self, leaf_hash: str, merkle_root: str) -> bool:
        return leaf_hash in self.leaves and self.root == merkle_root

    def export(self) -> dict:
        return {"leaves": list(self.leaves), "root": self.root, "leaf_count": len(self.leaves)}

    def get_leaf_count(self) -> int:
        return len(self.leaves)
