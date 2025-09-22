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
        self.cpu_seeds: Dict[str, str] = {}  # seed -> page_id mapping
        self.core_seeds: Dict[str, list] = {}  # char -> list of seeds that hash to that char
        self.cpu_iterations = CPU_PAGE_ITERATIONS
        self.core_iterations = CORE_PAGE_ITERATIONS_PER_CHAR
        self.page_id_length = PAGE_ID_LENGTH

    def load_cache(self) -> bool:
        """Load existing cache from file. Returns True if loaded successfully."""
        if not os.path.exists(self.cache_file):
            print(f"No cache file found at {self.cache_file}")
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

            print(f"Loaded cache: {len(self.cpu_seeds)} CPU seeds, {len(self.core_seeds)} core seeds")
            print(f"Cache iterations: CPU={self.cpu_iterations:,}, Core={self.core_iterations:,}")
            return True

        except Exception as e:
            print(f"Error loading cache: {e}")
            return False

    def save_cache(self) -> bool:
        """Save current cache to file. Returns True if saved successfully."""
        # Count total core seeds
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

            print(f"Saved cache: {len(self.cpu_seeds)} CPU seeds, {total_core_seeds} core seeds")
            return True

        except Exception as e:
            print(f"Error saving cache: {e}")
            return False

    def generate_random_seed(self) -> str:
        """Generate a random 16-character seed."""
        chars = string.digits + "abcdef"
        return ''.join(random.choices(chars, k=16))

    def hash_cpu_seed(self, seed: str) -> str:
        """Hash a CPU seed the required number of times to get page ID."""
        result = seed
        for _ in range(self.cpu_iterations):
            result = hashlib.md5(result.encode()).hexdigest()
        return result[:self.page_id_length]

    def hash_core_seed(self, seed: str) -> str:
        """Hash a core seed to get the first character."""
        result = seed
        for _ in range(self.core_iterations):
            result = hashlib.md5(result.encode()).hexdigest()
        return result[0]

    def ensure_cpu_seeds(self, needed: int, cpu_iterations: int = None) -> bool:
        """Ensure we have at least 'needed' CPU seeds. Generate more if necessary."""
        if cpu_iterations is not None:
            if cpu_iterations != self.cpu_iterations:
                print(f"CPU iteration count changed from {self.cpu_iterations:,} to {cpu_iterations:,}")
                print("Clearing CPU cache to regenerate with new iteration count")
                self.cpu_seeds.clear()
                self.cpu_iterations = cpu_iterations
        else:
            self.cpu_iterations = CPU_PAGE_ITERATIONS

        current_count = len(self.cpu_seeds)
        if current_count >= needed:
            print(f"Sufficient CPU seeds: {current_count}/{needed}")
            return True

        additional_needed = needed - current_count
        print(f"Generating {additional_needed} additional CPU seeds (have {current_count}/{needed})...")
        print(f"Each seed requires {self.cpu_iterations:,} hash iterations...")

        generated = 0
        start_time = time.time()

        while generated < additional_needed:
            seed = self.generate_random_seed()

            # Skip if we already have this seed
            if seed in self.cpu_seeds:
                continue

            if generated % 10 == 0:
                elapsed = time.time() - start_time
                rate = generated / elapsed if elapsed > 0 else 0
                eta = (additional_needed - generated) / rate if rate > 0 else 0
                print(f"  Progress: {current_count + generated}/{needed} seeds "
                      f"({rate:.1f} seeds/sec, ETA: {eta:.0f}s)")

            # Generate the page ID for this seed
            page_id = self.hash_cpu_seed(seed)
            self.cpu_seeds[seed] = page_id
            generated += 1

            # Save periodically
            if generated % 10 == 0:
                self.save_cache()

        self.save_cache()

        elapsed = time.time() - start_time
        print(f"Generated {generated} CPU seeds in {elapsed:.1f}s ({generated/elapsed:.2f} seeds/sec)")
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
            total_seeds = sum(len(seeds) for seeds in self.core_seeds.values())
            print(f"All characters have {CORE_SEEDS_PER_CHAR} seeds each with {total_seeds} total core seeds")
            return True

        print(f"Characters needing more seeds: {len(chars_needing_seeds)}")
        for char in chars_needing_seeds:
            current_count = len(self.core_seeds[char])
            needed = CORE_SEEDS_PER_CHAR - current_count
            print(f"  '{char}': has {current_count}, needs {needed} more")
        print(f"Generating core seeds (each requires {self.core_iterations:,} hash iterations)...")

        start_time = time.time()
        generated = 0
        attempts = 0
        last_save_time = start_time

        while chars_needing_seeds:
            seed = self.generate_random_seed()
            attempts += 1

            # Show progress
            if attempts % 100 == 0:
                elapsed = time.time() - start_time
                rate = generated / elapsed if elapsed > 0 else 0
                chars_complete = 16 - len(chars_needing_seeds)
                print(f"  Progress: {chars_complete}/16 chars have {CORE_SEEDS_PER_CHAR} seeds "
                      f"({generated} seeds, {attempts} attempts, {rate:.1f} seeds/sec)")

            # Hash the seed to get its target character
            target_char = self.hash_core_seed(seed)

            # Add to the appropriate list if it's a char that needs more seeds
            if target_char in chars_needing_seeds:
                self.core_seeds[target_char].append(seed)
                generated += 1
                current_count = len(self.core_seeds[target_char])
                print(f"  Found seed for '{target_char}': {seed} (now has {current_count}/{CORE_SEEDS_PER_CHAR})")

                # Remove from needing list if it now has enough
                if current_count >= CORE_SEEDS_PER_CHAR:
                    chars_needing_seeds.remove(target_char)

                # Save periodically
                if time.time() - last_save_time > 10:
                    self.save_cache()
                    last_save_time = time.time()
            else:
                # Also store seeds for chars that have room (build up pools)
                if len(self.core_seeds[target_char]) < CORE_SEEDS_PER_CHAR * 2:  # Allow up to 2x the required amount
                    self.core_seeds[target_char].append(seed)
                    generated += 1

        self.save_cache()

        elapsed = time.time() - start_time
        total_seeds = sum(len(seeds) for seeds in self.core_seeds.values())
        print(f"Generated {generated} core seeds in {elapsed:.1f}s")
        print(f"All 16 hex characters now have at least {CORE_SEEDS_PER_CHAR} seeds each ({total_seeds} total seeds)")
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

    def get_cpu_seeds_for_targets(self, target_page_ids: list, used_seeds: set = None) -> list:
        """Get CPU seeds that hash to the target page IDs."""
        if used_seeds is None:
            used_seeds = set()

        seeds = []
        available_targets = set(self.cpu_seeds.values())

        for target in target_page_ids:
            # Every target should have available seeds since all page IDs come from hashcache
            if target not in available_targets:
                raise ValueError(f"No CPU seed available for target {target} - this should never happen!")

            # Find an unused seed that maps to this target
            found_seed = False
            for seed, page_id in self.cpu_seeds.items():
                if page_id == target and seed not in used_seeds:
                    seeds.append(seed)
                    used_seeds.add(seed)
                    found_seed = True
                    break

            if not found_seed:
                # This means all seeds for this target are already used
                # For now, reuse the first available seed (could be improved with better seed management)
                for seed, page_id in self.cpu_seeds.items():
                    if page_id == target:
                        seeds.append(seed)
                        break
        return seeds

    def get_core_seeds_for_targets(self, target_page_ids: list, used_seeds: set = None) -> list:
        """Get hex-seed lists (lists of PAGE_ID_LENGTH seeds) that hash to the target page IDs."""
        if used_seeds is None:
            used_seeds = set()

        hex_seed_lists = []

        for target in target_page_ids:
            if len(target) < PAGE_ID_LENGTH:
                target = target.ljust(PAGE_ID_LENGTH, '0')

            # Build a hex-seed list for this target
            hex_seeds = []
            for char in target[:PAGE_ID_LENGTH]:
                hex_seeds.append(random.choice(self.core_seeds[char]))

            if len(hex_seeds) == PAGE_ID_LENGTH:
                hex_seed_lists.append(hex_seeds)

        return hex_seed_lists

    def generate_cache(self) -> bool:
        """Generate cache with seeds needed for current configuration"""
        print("HashCacher - Generating cache based on config.py settings")
        print(f"Configuration:")
        print(f"  TOTAL_PAGES: {TOTAL_PAGES}")
        print(f"  CPU_PAGE_PROBABILITY: {CPU_PAGE_PROBABILITY}")
        print(f"  CORE_PAGE_PROBABILITY: {CORE_PAGE_PROBABILITY}")
        print(f"  AVG_LINKS_PER_PAGE: {AVG_LINKS_PER_PAGE}")
        print(f"  CPU_PAGE_ITERATIONS: {CPU_PAGE_ITERATIONS:,}")
        print(f"  CORE_PAGE_ITERATIONS_PER_CHAR: {CORE_PAGE_ITERATIONS_PER_CHAR:,}")
        print()

        print("Calculated requirements:")
        print(f"  CPU seeds needed: {TOTAL_PAGES}")
        print(f"  Core seeds needed: {CORE_SEEDS_PER_CHAR} seeds per hex character (16 chars × {CORE_SEEDS_PER_CHAR} = {16 * CORE_SEEDS_PER_CHAR} total)")
        print()

        # Load existing cache
        self.load_cache()

        # Generate CPU and core seeds separately
        success = True
        if not self.ensure_cpu_seeds(TOTAL_PAGES, CPU_PAGE_ITERATIONS):
            success = False
        if not self.ensure_core_char_coverage():
            success = False

        if success:
            print(f"\n✓ Cache generation completed successfully!")
            info = self.get_cache_info()
            print(f"Final cache: {info['cpu_seeds']:,} CPU seeds, {info['core_seeds']:,} core seeds")
            print(f"Cache file: {self.cache_file}")
        else:
            print(f"\n✗ Cache generation failed!")

        return success


def main():
    """Generate hash cache based on config.py settings."""
    print("HashCacher - Reading configuration from config.py")

    # Validate configuration
    try:
        validate_config()
        print("✓ Configuration validated")
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        exit(1)

    # Create hash cacher instance
    cacher = HashCacher("hashcache.json")

    # Generate cache based on config
    success = cacher.generate_cache()

    if not success:
        exit(1)


if __name__ == "__main__":
    main()