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
        self.cpu_seeds: Dict[str, str] = {}
        self.core_seeds: Dict[str, str] = {}
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

            # Convert core_seeds from string keys back to tuples
            core_seeds_raw = cache.get("core_seeds", {})
            self.core_seeds = {}
            for key, value in core_seeds_raw.items():
                if "|" in key:  # New format with tuple keys
                    quad_seeds = tuple(key.split("|"))
                    self.core_seeds[quad_seeds] = value
                else:  # Old format with single seed keys - skip
                    continue

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
        # Convert core_seeds tuples to strings for JSON serialization
        core_seeds_serializable = {}
        for quad_seeds, quad_result in self.core_seeds.items():
            key = "|".join(quad_seeds)  # Join tuple with pipe separator
            core_seeds_serializable[key] = quad_result

        cache = {
            "cpu_seeds": self.cpu_seeds,
            "core_seeds": core_seeds_serializable,
            "generated_at": time.time(),
            "cpu_iterations": self.cpu_iterations,
            "core_iterations": self.core_iterations,
            "page_id_length": self.page_id_length,
            "total_cpu_seeds": len(self.cpu_seeds),
            "total_core_seeds": len(self.core_seeds)
        }

        try:
            # Write to temporary file first, then rename for atomic operation
            temp_file = f"{self.cache_file}.tmp"
            with open(temp_file, 'w') as f:
                json.dump(cache, f, indent=2)
            os.rename(temp_file, self.cache_file)

            print(f"Saved cache: {len(self.cpu_seeds)} CPU seeds, {len(self.core_seeds)} core seeds")
            return True

        except Exception as e:
            print(f"Error saving cache: {e}")
            return False

    def generate_random_seed(self) -> str:
        """Generate a random 16-character seed."""
        chars = string.ascii_lowercase + string.digits
        return ''.join(random.choices(chars, k=16))

    def hash_cpu_seed(self, seed: str) -> str:
        """Hash a CPU seed the required number of times to get page ID."""
        result = seed
        for i in range(self.cpu_iterations):
            result = hashlib.md5(f"{result}_{i}".encode()).hexdigest()
        return result[:self.page_id_length]

    def hash_core_quad(self, seeds: tuple) -> str:
        """Hash a tuple of 4 core seeds to get 4 characters."""
        result = ""
        for seed in seeds:
            seed_result = seed
            for i in range(self.core_iterations):
                seed_result = hashlib.md5(f"{seed_result}_{i}".encode()).hexdigest()
            result += seed_result[0]
        return result

    def ensure_cpu_seeds(self, needed: int, cpu_iterations: int = None) -> bool:
        """Ensure we have at least 'needed' CPU seeds. Generate more if necessary."""
        if cpu_iterations is not None:
            # Check if iteration count changed
            if cpu_iterations != self.cpu_iterations:
                print(f"CPU iteration count changed from {self.cpu_iterations:,} to {cpu_iterations:,}")
                print("Clearing CPU cache to regenerate with new iteration count")
                self.cpu_seeds.clear()
                self.cpu_iterations = cpu_iterations
        else:
            # Use config value
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

            # Skip if we already have this seed (unlikely with 16-char random)
            if seed in self.cpu_seeds:
                continue

            if generated % 10 == 0:  # Show progress
                elapsed = time.time() - start_time
                rate = generated / elapsed if elapsed > 0 else 0
                eta = (additional_needed - generated) / rate if rate > 0 else 0
                print(f"  Progress: {current_count + generated}/{needed} seeds "
                      f"({rate:.1f} seeds/sec, ETA: {eta:.0f}s)")

            # Generate the page ID for this seed
            page_id = self.hash_cpu_seed(seed)
            self.cpu_seeds[seed] = page_id
            generated += 1

            # Save periodically to prevent loss
            if generated % 10 == 0:
                self.save_cache()

        # Final save
        self.save_cache()

        elapsed = time.time() - start_time
        print(f"Generated {generated} CPU seeds in {elapsed:.1f}s ({generated/elapsed:.2f} seeds/sec)")
        return generated == additional_needed

    def ensure_core_seeds(self, needed: int, core_iterations: int = None) -> bool:
        """Ensure we have at least 'needed' core seeds. Generate more if necessary."""
        if core_iterations is not None:
            # Check if iteration count changed
            if core_iterations != self.core_iterations:
                print(f"Core iteration count changed from {self.core_iterations:,} to {core_iterations:,}")
                print("Clearing core cache to regenerate with new iteration count")
                self.core_seeds.clear()
                self.core_iterations = core_iterations
        else:
            # Use config value
            self.core_iterations = CORE_PAGE_ITERATIONS_PER_CHAR

        current_count = len(self.core_seeds)
        if current_count >= needed:
            print(f"Sufficient core seeds: {current_count}/{needed}")
            return True

        additional_needed = needed - current_count
        print(f"Generating {additional_needed} additional core seeds (have {current_count}/{needed})...")
        print(f"Each seed requires {self.core_iterations:,} hash iterations...")

        generated = 0
        start_time = time.time()

        while generated < additional_needed:
            # Generate a tuple of 4 random seeds
            quad_seeds = tuple(self.generate_random_seed() for _ in range(4))

            # Skip if we already have this quad (extremely unlikely)
            if quad_seeds in self.core_seeds:
                continue

            if generated % 10 == 0:  # Show progress
                elapsed = time.time() - start_time
                rate = generated / elapsed if elapsed > 0 else 0
                eta = (additional_needed - generated) / rate if rate > 0 else 0
                print(f"  Progress: {current_count + generated}/{needed} seeds "
                      f"({rate:.1f} quads/sec, ETA: {eta:.0f}s)")

            # Generate the 4-character result for this quad
            quad_result = self.hash_core_quad(quad_seeds)
            self.core_seeds[quad_seeds] = quad_result
            generated += 1

            # Save periodically to prevent loss
            if generated % 10 == 0:
                self.save_cache()

        # Final save
        self.save_cache()

        elapsed = time.time() - start_time
        print(f"Generated {generated} core seeds in {elapsed:.1f}s ({generated/elapsed:.2f} seeds/sec)")
        return generated == additional_needed

    def get_cache_info(self) -> Dict:
        """Get information about current cache state."""
        return {
            "cpu_seeds": len(self.cpu_seeds),
            "core_seeds": len(self.core_seeds),
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
            # Only provide seeds for targets we actually have seeds for
            if target in available_targets:
                # Find an unused seed that maps to this target
                for seed, page_id in self.cpu_seeds.items():
                    if page_id == target and seed not in used_seeds:
                        seeds.append(seed)
                        used_seeds.add(seed)
                        break
        return seeds

    def get_core_seeds_for_targets(self, target_page_ids: list, used_quads: set = None) -> list:
        """Get core seed groups (tuples of 4 seeds each) that hash to the target page IDs."""
        if used_quads is None:
            used_quads = set()

        seed_groups = []

        for target in target_page_ids:
            if len(target) < 4:
                target = target.ljust(4, '0')

            # Find a quad that produces this target
            found_quad = False
            for quad_seeds, quad_result in self.core_seeds.items():
                if quad_result == target[:4] and quad_seeds not in used_quads:
                    seed_groups.append(list(quad_seeds))
                    used_quads.add(quad_seeds)
                    found_quad = True
                    break

            if not found_quad:
                # Couldn't find a quad for this target, skip it
                continue

        return seed_groups

    def calculate_needed_seeds(self) -> tuple:
        """Calculate how many seeds we need for CPU and core pages"""
        cpu_pages = int(TOTAL_PAGES * CPU_PAGE_PROBABILITY)
        core_pages = int(TOTAL_PAGES * CORE_PAGE_PROBABILITY)

        # Each page has average links
        cpu_seeds_needed = cpu_pages * AVG_LINKS_PER_PAGE
        # For core: we need quads (each quad is one page ID)
        core_seeds_needed = core_pages * AVG_LINKS_PER_PAGE

        # Add 10% buffer
        cpu_seeds_needed = int(cpu_seeds_needed * 1.1)
        core_seeds_needed = int(core_seeds_needed * 1.1)

        return cpu_seeds_needed, core_seeds_needed

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

        # Calculate needed seeds
        cpu_needed, core_needed = self.calculate_needed_seeds()
        print(f"Calculated requirements:")
        print(f"  CPU seeds needed: {cpu_needed:,}")
        print(f"  Core seeds needed: {core_needed:,}")
        print()

        # Load existing cache
        self.load_cache()

        # Generate seeds
        success = True
        success &= self.ensure_cpu_seeds(cpu_needed)
        success &= self.ensure_core_seeds(core_needed)

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