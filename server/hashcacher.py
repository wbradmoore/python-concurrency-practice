#!/usr/bin/env python3
"""
HashCacher - Persistent hash seed cache management for the web graph server.

This module manages the generation and storage of hash seeds that map to page IDs.
Can be used standalone to pre-generate cache files or imported by the server.
All configuration is read from config.py.

Usage:
    python hashcacher.py
"""

import hashlib
import json
import os
import random
import string
import time
from typing import Dict

from config import *


class HashCacher:
    """Manages persistent hash seed cache with automatic expansion."""

    def __init__(self, cache_file: str = "hashcache.json"):
        self.cache_file = cache_file
        self.cpu_seeds: Dict[str, str] = {}  # page_id -> seed mapping
        self.core_seeds: Dict[str, list] = {}  # char -> list of seeds that hash to that char
        self.cpu_iterations = CPU_PAGE_ITERATIONS
        self.core_iterations = CORE_PAGE_ITERATIONS_PER_CHAR
        self.page_id_length = PAGE_ID_LENGTH

    def load_cache(self) -> bool:
        """Load existing cache from file. Returns True if loaded successfully."""
        if not os.path.exists(self.cache_file):
            return False

        try:
            with open(self.cache_file, 'r') as f:
                cache = json.load(f)

            self.cpu_seeds = cache.get("cpu_seeds", {})

            # Handle both old and new core_seeds format
            core_seeds_raw = cache.get("core_seeds", {})
            if core_seeds_raw:
                # Check if it's the new format (char -> list of seeds)
                first_key = list(core_seeds_raw.keys())[0] if core_seeds_raw else None
                if first_key and len(first_key) == 1:
                    # New format: single char keys
                    self.core_seeds = core_seeds_raw
                else:
                    # Old format: need to convert or clear
                    print("Old core_seeds format detected, will regenerate")
                    self.core_seeds = {}

            # Load iteration counts from cache if available
            self.cpu_iterations = cache.get("cpu_iterations", self.cpu_iterations)
            self.core_iterations = cache.get("core_iterations", self.core_iterations)

            return True

        except Exception:
            return False

    def save_cache(self) -> bool:
        """Save current cache to file. Returns True if saved successfully."""
        total_core_seeds = sum(len(seeds) for seeds in self.core_seeds.values())

        cache = {
            "cpu_seeds": self.cpu_seeds,
            "core_seeds": self.core_seeds,
            "generated_at": time.time(),
            "cpu_iterations": self.cpu_iterations,
            "core_iterations": self.core_iterations,
            "page_id_length": self.page_id_length,
            "total_cpu_seeds": len(self.cpu_seeds),
            "total_core_seeds": total_core_seeds
        }

        try:
            # Write to temporary file first, then rename for atomic operation
            temp_file = f"{self.cache_file}.tmp"
            with open(temp_file, 'w') as f:
                json.dump(cache, f, indent=2)
            os.rename(temp_file, self.cache_file)

            return True

        except Exception:
            return False

    def generate_random_seed(self) -> str:
        """Generate a random 16-character seed."""
        chars = string.digits + "abcdef"
        return ''.join(random.choices(chars, k=16))

    def hash_cpu_seed(self, seed: str) -> str:
        for _ in range(self.cpu_iterations):
            seed = hashlib.md5(seed.encode()).hexdigest()
        return seed[:self.page_id_length]

    def hash_core_seed(self, seed: str) -> str:
        for _ in range(self.core_iterations):
            seed = hashlib.md5(seed.encode()).hexdigest()
        return seed[0]

    def ensure_cpu_seeds(self, needed: int, cpu_iterations: int = None) -> bool:
        """Ensure we have at least 'needed' CPU seeds. Generate more if necessary."""
        if cpu_iterations is not None:
            if cpu_iterations != self.cpu_iterations:
                self.cpu_seeds.clear()
                self.cpu_iterations = cpu_iterations
        else:
            self.cpu_iterations = CPU_PAGE_ITERATIONS

        current_count = len(self.cpu_seeds)
        if current_count >= needed:
            return True

        needed -= current_count

        while needed:
            seed = self.generate_random_seed()

            # Generate the page ID for this seed
            page_id = self.hash_cpu_seed(seed)

            # Skip if we already have this page_id
            if page_id in self.cpu_seeds:
                continue

            self.cpu_seeds[page_id] = seed
            needed -= 1

            self.save_cache()

        return True

    def ensure_core_char_coverage(self) -> bool:
        """Ensure we have at least one seed for each possible hex character (0-9, a-f)."""
        all_chars = string.digits + "abcdef"

        # Initialize core_seeds dict if needed
        for char in all_chars:
            if char not in self.core_seeds:
                self.core_seeds[char] = []

        # Check which characters need more seeds
        chars_needing_seeds = []
        for char in all_chars:
            if len(self.core_seeds[char]) < CORE_SEEDS_PER_CHAR:
                chars_needing_seeds.append(char)

        if not chars_needing_seeds:
            return True


        while chars_needing_seeds:
            seed = self.generate_random_seed()

            # Hash the seed to get its target character
            target_char = self.hash_core_seed(seed)

            # Add to the appropriate list if it's a char that needs more seeds
            if target_char in chars_needing_seeds:
                self.core_seeds[target_char].append(seed)
                current_count = len(self.core_seeds[target_char])

                # Remove from needing list if it now has enough
                if current_count >= CORE_SEEDS_PER_CHAR:
                    chars_needing_seeds.remove(target_char)

            else:
                # Also store seeds for chars that have room (build up pools)
                if len(self.core_seeds[target_char]) < CORE_SEEDS_PER_CHAR * 2:  # Allow up to 2x the required amount
                    self.core_seeds[target_char].append(seed)

            self.save_cache()

        return True

    def get_cache_info(self) -> Dict:
        """Get information about current cache state."""
        total_core_seeds = sum(len(seeds) for seeds in self.core_seeds.values())
        chars_covered = len([c for c in self.core_seeds if self.core_seeds[c]])

        return {
            "cpu_seeds": len(self.cpu_seeds),
            "core_seeds": total_core_seeds,
            "chars_covered": chars_covered,
            "cpu_iterations": self.cpu_iterations,
            "core_iterations": self.core_iterations,
            "cache_file": self.cache_file,
            "file_exists": os.path.exists(self.cache_file)
        }

    def get_cpu_seeds_for_targets(self, target_page_ids: list) -> list:
        """Get CPU seeds that hash to the target page IDs."""
        seeds = []

        for target in target_page_ids:
            # Get the seed for this target page ID
            if target in self.cpu_seeds:
                seeds.append(self.cpu_seeds[target])
        return seeds

    def get_core_seeds_for_targets(self, target_page_ids: list) -> list:
        """Get hex-seed lists (lists of PAGE_ID_LENGTH seeds) that hash to the target page IDs."""

        hex_seed_lists = []

        for target in target_page_ids:
            # Build a hex-seed list for this target
            hex_seeds = []
            for char in target:
                hex_seeds.append(random.choice(self.core_seeds[char]))
            hex_seed_lists.append(hex_seeds)

        return hex_seed_lists

    def generate_cache(self) -> bool:
        """Generate cache with seeds needed for current configuration"""

        # Load existing cache
        self.load_cache()

        # Generate CPU and core seeds separately
        success = True
        if not self.ensure_cpu_seeds(TOTAL_PAGES, CPU_PAGE_ITERATIONS):
            success = False
        if not self.ensure_core_char_coverage():
            success = False


        return success


def main():
    """Generate hash cache based on config.py settings."""
    validate_config()
    cacher = HashCacher("hashcache.json")
    cacher.generate_cache()


if __name__ == "__main__":
    main()