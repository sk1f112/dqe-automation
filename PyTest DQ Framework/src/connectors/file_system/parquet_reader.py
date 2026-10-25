"""Read Parquet files and partitioned Parquet datasets."""

from pathlib import Path

import pandas as pd


class ParquetReader:
    """Load a Parquet file or dataset into a pandas DataFrame."""

    def process(self, path: str, include_subfolders: bool = False) -> pd.DataFrame:
        parquet_path = Path(path)
        if not parquet_path.exists():
            raise FileNotFoundError(f"Parquet path does not exist: {parquet_path}")

        if parquet_path.is_file():
            if parquet_path.suffix.lower() != ".parquet":
                raise ValueError(f"Expected a .parquet file: {parquet_path}")
            return pd.read_parquet(parquet_path)

        if include_subfolders:
            return pd.read_parquet(parquet_path)

        parquet_files = sorted(
            item
            for item in parquet_path.iterdir()
            if item.is_file() and item.suffix.lower() == ".parquet"
        )
        if not parquet_files:
            raise FileNotFoundError(
                f"No Parquet files found directly in dataset directory: {parquet_path}"
            )
        frames = [pd.read_parquet(file_path) for file_path in parquet_files]
        return pd.concat(frames, ignore_index=True)
