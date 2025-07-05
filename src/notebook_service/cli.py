# src/cli.py
from typing import Optional

import pandas as pd

from .emotion import get_analysis


def analyze_df(df: pd.DataFrame, text_column: str) -> pd.DataFrame:
    """
    Pure function: takes a DataFrame + name of the text column,
    returns a new DataFrame with emotion, concepts & semantic-roles merged in.
    """
    # Keep the NLU output as-is, then drop the 'text' column
    texts = df[text_column].astype(str).tolist()
    df_analysis = get_analysis(texts).drop(columns=["text"])

    # concatenate side-by-side (resetting indices to align rows)
    return pd.concat(
        [df.reset_index(drop=True), df_analysis.reset_index(drop=True)],
        axis=1
    )


def main(input_csv: str, text_column: str, output_csv: Optional[str] = None):
    """I/O wrapper: reads CSV, calls analyze_df, writes or prints result."""
    df = pd.read_csv(input_csv)
    df_out = analyze_df(df, text_column)

    if output_csv:
        df_out.to_csv(output_csv, index=False, encoding="utf-8-sig")
        print(f"Wrote analysis to {output_csv}")
    else:
        print(df_out.to_string(index=False))


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--input", "-i", required=True, help="path to input CSV")
    p.add_argument("--column", "-c", required=True, help="text column name")
    p.add_argument("--output", "-o", help="where to write (optional)")
    args = p.parse_args()
    main(args.input, args.column, args.output)
